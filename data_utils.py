'''
This script contains several functions used for data processing.
'''

#############################################################################
# Import here useful libraries
#############################################################################
from nltk.tokenize import word_tokenize
import tensorflow as tf
import pandas as pd
import pickle
import random
import glob
import nltk
import re

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


def imdb2tfrecords(path_data='datasets/aclImdb/', min_word_frequency=5,
                   max_words_review=700):
    '''
    This script processes the data and saves it in the default TensorFlow 
    file format: tfrecords.
    
    Args:
        path_data: the path where the imdb data is stored.
        min_word_frequency: the minimum frequency of a word, to keep it
                            in the vocabulary.
        max_words_review: the maximum number of words allowed in a review.
    '''
    # Get the filenames of the positive/negative reviews we will use
    # for training the RNN
    train_pos_files = glob.glob(path_data + 'train/pos/*')
    train_neg_files = glob.glob(path_data + 'train/neg/*')

    # Concatenate both positive and negative reviews filenames
    train_files = train_pos_files + train_neg_files
    
    # List with all the reviews in the train dataset
    reviews = [open(train_files[i],'r').read() for i in range(len(train_files))]
    
    # Remove HTML tags
    reviews = [re.sub(r'<[^>]+>', ' ', review) for review in reviews]
        
    # Tokenize each review in part
    reviews = [word_tokenize(review) for review in reviews]
    
    # Compute the length of each review
    len_reviews = [len(review) for review in reviews]
    pickle.dump(len_reviews, open(path_data + 'length_reviews.pkl', 'wb'))

    # Flatten nested list
    reviews = [word for review in reviews for word in review]
    
    # Compute the frequency of each word
    word_frequency = pd.value_counts(reviews)
    
    # Keep only words with frequency higher than minimum
    vocabulary = word_frequency[word_frequency>=min_word_frequency].index.tolist()
    
    # Add Unknown, Start and End token. 
    extra_tokens = ['Unknown_token', 'End_token']
    vocabulary += extra_tokens
    
    # Create a word2idx dictionary
    word2idx = {vocabulary[i]: i for i in range(len(vocabulary))}
    
    # Write word vocabulary to disk
    pickle.dump(word2idx, open(path_data + 'word2idx.pkl', 'wb'))
        
    def text2tfrecords(filenames, writer, vocabulary, word2idx,
                       max_words_review):
        '''
        Function to parse each review in part and write to disk
        as a tfrecord.
        
        Args:
            filenames: the paths of the review files.
            writer: the writer object for tfrecords.
            vocabulary: list with all the words included in the vocabulary.
            word2idx: dictionary of words and their corresponding indexes.
        '''
        # Shuffle filenames
        random.shuffle(filenames)
        for filename in filenames:
            review = open(filename, 'r').read()
            review = re.sub(r'<[^>]+>', ' ', review)
            review = word_tokenize(review)
            # Reduce review to max words
            review = review[-max_words_review:]
            # Replace words with their equivalent index from word2idx
            review = [word2idx[word] if word in vocabulary else 
                      word2idx['Unknown_token'] for word in review]
            indexed_review = review + [word2idx['End_token']]
            sequence_length = len(indexed_review)
            target = 1 if filename.split('/')[-2]=='pos' else 0
            # Create a Sequence Example to store our data in
            ex = tf.train.SequenceExample()
            # Add non-sequential features to our example
            ex.context.feature['sequence_length'].int64_list.value.append(sequence_length)
            ex.context.feature['target'].int64_list.value.append(target)
            # Add sequential feature
            token_indexes = ex.feature_lists.feature_list['token_indexes']
            for token_index in indexed_review:
                token_indexes.feature.add().int64_list.value.append(token_index)
            writer.write(ex.SerializeToString())
    
    ##########################################################################     
    # Write train data to tfrecords.This might take a while (~10 minutes)
    ##########################################################################
    train_writer = tf.python_io.TFRecordWriter(path_data + 'train.tfrecords')
    text2tfrecords(train_files, train_writer, vocabulary, word2idx, 
                   max_words_review)

    ##########################################################################
    # Get the filenames of the reviews we will use for testing the RNN 
    ##########################################################################
    test_pos_files = glob.glob(path_data + 'test/pos/*')
    test_neg_files = glob.glob(path_data + 'test/neg/*')
    test_files = test_pos_files + test_neg_files

    ##########################################################################
    # Write test data to tfrecords (~10 minutes)
    ##########################################################################
    test_writer = tf.python_io.TFRecordWriter('datasets/aclImdb/test.tfrecords')
    text2tfrecords(test_files, test_writer, vocabulary, word2idx,
                   max_words_review)


def parse_imdb_sequence(record):
    '''
    Script to parse imdb tfrecords.
    
    Returns:
        token_indexes: sequence of token indexes present in the review.
        target: the target of the movie review.
        sequence_length: the length of the sequence.
    '''
    context_features = {
        'sequence_length': tf.FixedLenFeature([], dtype=tf.int64),
        'target': tf.FixedLenFeature([], dtype=tf.int64),
        }
    sequence_features = {
        'token_indexes': tf.FixedLenSequenceFeature([], dtype=tf.int64),
        }
    context_parsed, sequence_parsed = tf.parse_single_sequence_example(record, 
        context_features=context_features, sequence_features=sequence_features)
        
    return (sequence_parsed['token_indexes'], context_parsed['target'],
            context_parsed['sequence_length'])

     
        
