# news_sentiment_model.py

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Optionally map numeric news codes to textual snippets
NEWS_TEXT_MAPPING = {
    0: "",
    50: "Positive news sentiment detected.",
    100: "Strong positive news sentiment.",
    # Add more mappings as needed...
}

class FinBertSentimentModel:
    def __init__(self, pretrained_model="ProsusAI/finbert"):
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(pretrained_model)
        self.model.eval()

    def get_sentiment_signal(self, description: str, news_value: str) -> int:
        """
        Combines the description and an optional text snippet (based on the news code)
        and returns a sentiment signal:
            +1 for positive sentiment,
             0 for neutral,
            -1 for negative sentiment.
        """
        try:
            news_code = int(news_value)
        except ValueError:
            news_code = 0

        snippet = NEWS_TEXT_MAPPING.get(news_code, "")
        combined_text = (description + " " + snippet).strip()

        # If no combined text, default to neutral
        if not combined_text:
            return 0

        # Tokenize input text (with truncation to avoid too-long sequences)
        inputs = self.tokenizer(combined_text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits.detach().numpy()[0]

        # For the ProsusAI/finbert model, we assume:
        # Index 0: positive, Index 1: neutral, Index 2: negative.
        predicted_class = int(np.argmax(logits))
        if predicted_class == 0:
            return 1
        elif predicted_class == 1:
            return 0
        else:
            return -1
