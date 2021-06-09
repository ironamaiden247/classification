import csv
import spacy
from collections import Counter


# Import Coals_clean_correlation.csv -- DONE
# Format is (label, keywords) -- DONE
# Filter out labels (whole row) which are stopwords, not nouns -- DONE
# Add column to ccc - frequency of noun appearance in DatasetSemanticSimilarity.csv -- DONE
# First 10 become high priority, used for classification
# Next 10, 'others'
# Remainder: 'misc'
# Add column to ccc, label type determined by https://spacy.io/api/annotation#named-entities -- DONE

nlp = spacy.load('en_core_web_sm')

# Update these to the correct input/output file paths
ccc_path = 'C:\\Saurabh\\Coals_325.csv'
dss_path = 'C:\\Saurabh\\Reviews325_unified.csv'
out_path = 'C:\\Saurabh\\Freq_ParetoScore3.csv'

# Create a histogram of words appearing in the dss file
with open(dss_path) as dss_file:
    next(dss_file)  # Skip header line
    all_dss_words = []
    for line in dss_file:
        all_dss_words.extend(line.split())
dss_histogram = Counter(all_dss_words)

# output is a list of tuples, where each tuple is (original_label, entity, count, original_keywords)
output = []

with open(ccc_path) as ccc_file:
    next(ccc_file)  # Skip header line
    csv_reader = csv.reader(ccc_file, delimiter=',')
    for row in csv_reader:
        label_doc = nlp(row[0]) # Analyse label with spaCy
        if not label_doc[0].is_stop:
            if label_doc[0].pos == spacy.symbols.NOUN:
                # Combine counts of 'raw' and lemmatized noun
                count = max(dss_histogram[row[0]], dss_histogram[label_doc[0].lemma_])
                # Provide a default value if entity isn't recognised
                entity = label_doc.ents[0].label_ if len(label_doc.ents) > 0 else 'NONE'

                output.append((row[0], entity, count, ' '.join(row[1].split())))
        ### Uncomment the following to see the extra filtering provided by lemmatization
        # elif row[0] not in spacy.lang.en.stop_words.STOP_WORDS:
        #     print('{}, {}, {}'.format(row[0], doc[0].text, doc[0].lemma_))

# Sort output by label occurrence in dss file
sorted_output = sorted(output, key=lambda r: r[2], reverse=True)

with open(out_path, mode='w', newline='') as out_file:
    csv_writer = csv.writer(out_file, delimiter=',', quotechar='"')
    for row in sorted_output:
        csv_writer.writerow(row)
