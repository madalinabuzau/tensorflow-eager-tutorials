'''
This script contains several functions used for data processing.
'''

# Import here useful libraries
from nltk.tokenize import word_tokenize
import tensorflow as tf
import re

def text2tfrecords(filenames, writer, word2idx, vocabulary):
    for filename in filenames:
        review = open(filename, 'r').read()
        review = re.sub(r'<[^>]+>', ' ', review)
        review = word_tokenize(review)
        # Replace words with their equivalent index from word2idx
        indexed_review = ([word2idx['Start_token']] + [word2idx[word] if word 
            in vocabulary else word2idx['Unknown_token'] for word in review] + 
            [word2idx['End_token']])
        sequence_length = len(indexed_review)
        target = 1 if filename.split('/')[-2]=='pos' else 0
        score = int(filename.split('_')[-1].split('.')[0])
        # Create a Sequence Example to store our data in
        ex = tf.train.SequenceExample()
        # Add non-sequential features to our example
        ex.context.feature['sequence_length'].int64_list.value.append(sequence_length)
        ex.context.feature['target'].int64_list.value.append(target)
        ex.context.feature['score'].int64_list.value.append(score)
        # Add sequential feature
        words_indexes = ex.feature_lists.feature_list['words_indexes']
        for word_index in indexed_review:
            words_indexes.feature.add().int64_list.value.append(word_index)
        writer.write(ex.SerializeToString())

     
        
