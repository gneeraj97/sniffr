def load_keywords(file_path):
    with open(file_path, 'r') as file:
        return [word.strip().lower() for word in file]

def calculate_score(content, keywords, dont_bother_words):
    content = content.lower()

    # Count occurrences of interesting keywords
    keyword_count = sum(content.count(keyword) for keyword in keywords)

    # Count occurrences of 'dont_bother' keywords
    dont_bother_count = sum(content.count(word) for word in dont_bother_words)

    # Calculate raw score
    raw_score = keyword_count - (dont_bother_count * 1.5)

    # Normalize score to 0-100 range
    max_expected_score = 20  # Adjust this based on your expected maximum raw score
    normalized_score = max(min(raw_score / max_expected_score * 100, 100), 0)

    return round(normalized_score, 2)

def get_interest_flag(score):
    if score < 10:
        return "Don't bother"
    elif score > 60:
        return "Interesting"
    else:
        return "Not Interesting"
    
if __name__ =="__main__":
    print("This is a helper script.")