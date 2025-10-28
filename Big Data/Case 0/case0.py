import pandas as pd
import re
from collections import Counter

# The full movie quote
text = """Crom, I have never prayed to you before. I have no tongue for it.
No one, not even you, will remember if we were good men or bad, why we fought, or why we died.
All that matters is that two stood against many. That’s what’s important.
Valor pleases you, Crom… so grant me one request. Grant me revenge!
And if you do not listen, then to hell with you!"""

# 1. Split text into sentences
sentences = [s.strip() for s in re.split(r'[.!]+', text) if s.strip()]

# 2. Build word lists per sentence
sent_words = [re.findall(r'\b\w+\b', s.lower()) for s in sentences]

# 3. Count words per sentence
sentence_counts = [Counter(words) for words in sent_words]

# 4. Global word count (for Column E)
global_counts = Counter(word for words in sent_words for word in words)

# 5. Column A: full text
col_a = [text] + [""] * (len(sentences) - 1)

# 6. Column B: split sentences
col_b = sentences

# 7. Column C: per-sentence word counts in "word, count" format
col_c = [", ".join(f"{w}, {c}" for w, c in sorted(cnt.items())) for cnt in sentence_counts]

# 8. Column D: one row per word occurrence (repeated by total occurrences)
col_d = []
for word, count in global_counts.items():
    col_d.extend([word] * count)

# 9. Column E: unique words with total count in "word, count" format
col_e = [f"{w}, {c}" for w, c in sorted(global_counts.items())]

# 10. Construct dataframe
max_len = max(len(col_a), len(col_b), len(col_c), len(col_d), len(col_e))
pad = lambda lst: lst + [""] * (max_len - len(lst))
data = {
    "Input": pad(col_a),
    "Split": pad(col_b),
    "Per Sentence Counts": pad(col_c),
    "Group (Each Word)": pad(col_d),
    "Global Key-Value Pairs": pad(col_e)
}
df = pd.DataFrame(data)

# 11. Write to Excel
df.to_excel("movie_text_analysis.xlsx", index=False)

print(df)
