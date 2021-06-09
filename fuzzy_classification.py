import csv
from typing import Dict
import editdistance
import sqlite3


# Use function of Levenshtein distance and word length to assign score, then compare to threshold
def compare_fuzzy(text_1: str, text_2: str, threshold: float) -> Dict:
    t1_len = len(text_1)
    t2_len = len(text_2)
    larger = t1_len if t1_len >= t2_len else t2_len
    delta = editdistance.eval(text_1, text_2)
    if delta >= larger:
        score = 0.0
    else:
        score = 1 - (delta / larger)

    if score >= threshold:
        output = {'pass': True, 'score': score}
    else:
        output = {'pass': False, 'score': score}

    return output


# Iterates over object but terminates 1 item from the end
def skip_last(iterator):
    prev = next(iterator)
    for item in iterator:
        yield prev
        prev = item


def process(freq_pareto_path, review_text_path, database_path, match_threshold, max_categories):
    db = sqlite3.connect(database_path)
    db.execute('DELETE FROM categories')
    db.execute('DELETE FROM reviews')
    db.execute('DELETE FROM matches')
    db.commit()

    with open(review_text_path, encoding="utf8") as review_text_file:
        next(review_text_file)  # Skip header line
        reviews = []
        for line in review_text_file:
            db.execute('INSERT INTO reviews (words) VALUES (?)', [line])
            reviews.append(line.split())

    with open(freq_pareto_path) as freq_pareto_file:
        next(freq_pareto_file)  # Skip header line
        csv_reader = csv.reader(freq_pareto_file, delimiter=',')
        nouns_verbs = []
        for line in skip_last(csv_reader):
            nouns_verbs.append((line[0], line[4].split()))
            db.execute('INSERT INTO categories (noun, associated) VALUES (?, ?)', [line[0], line[4]])
            if len(nouns_verbs) >= max_categories:
                break

    # A noun associates with a review if any of the reviews words fuzzy match to it
    review_matches = []
    done = 0
    for i_n, nv in enumerate(nouns_verbs):
        all_words = [nv[0]]
        all_words.extend(nv[1])
        matched = []
        for i_r, review_words in enumerate(reviews):
            for word in review_words:
                for w in all_words:
                    if compare_fuzzy(w, word, match_threshold)['pass']:
                        # ## Uncomment to help tune the threshold parameter
                        # print('matched: {}, {}'.format(w, word))
                        matched.append(' '.join(review_words))
                        db.execute('INSERT INTO matches VALUES (?, ?)', [i_n + 1, i_r + 1])
                        break
                else:
                    continue
                break

        review_matches.append((nv[0], matched))
        done += 1
        print('{}/{}'.format(done, len(nouns_verbs)))
        print('{}: {}'.format(nv[0], len(matched)))

    db.commit()
    db.close()

    print('=== fuzzy process complete ===\n')


def analyse(database_path):
    db = sqlite3.connect(database_path)
    cur = db.cursor()
    total = cur.execute('SELECT count(*) FROM reviews')
    for t in total:
        print('Total Reviews: {}'.format(t[0]))
    counts = cur.execute('SELECT categories.noun, count(matches.review_id) AS c FROM categories INNER JOIN matches ON (categories.id = matches.category_id) GROUP BY categories.id ORDER BY c DESC')
    for count in counts:
        print('{}: {}'.format(count[0], count[1]))
    other = cur.execute('SELECT * FROM reviews LEFT JOIN matches ON (reviews.id = matches.review_id) WHERE matches.review_id IS NULL')
    others = other.fetchall()
    print('Others: {}'.format(len(others)))
    db.close()

