"""Text normalization and typo correction using Levenshtein distance."""

from rapidfuzz import fuzz, process
from .keywords import ALL_KEYWORDS


class TextNormalizer:
    """Normalizes user input and corrects typos."""

    def __init__(self, max_distance=2):
        """
        Initialize normalizer.

        Args:
            max_distance: Maximum Levenshtein distance for typo correction (default: 2)
        """
        self.max_distance = max_distance
        self.corrections = {}

    def normalize(self, text):
        """
        Normalize text: lowercase, strip, handle smart characters.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower().strip()

        # Replace smart/curly quotes with straight quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('„', '"').replace('"', '"')

        # Replace various dash characters with standard hyphen
        text = text.replace('–', '-')
        text = text.replace('—', '-')
        text = text.replace('−', '-')

        # Replace non-breaking spaces with regular spaces
        text = text.replace('\u00A0', ' ')
        text = text.replace('\u202F', ' ')

        # Normalize multiple spaces to single space
        import re
        text = re.sub(r'\s+', ' ', text)

        return text

    def correct_typos(self, text):
        """
        Correct typos in text using Levenshtein distance.

        Args:
            text: Normalized input text

        Returns:
            Tuple of (corrected_text, corrections_dict)
            where corrections_dict maps original_word -> corrected_word
        """
        words = text.split()
        corrected_words = []
        corrections = {}

        for word in words:
            # Skip numbers and short words
            if word.isdigit() or len(word) <= 2:
                corrected_words.append(word)
                continue

            # Skip if word is already a known keyword
            if word in ALL_KEYWORDS:
                corrected_words.append(word)
                continue

            # Try to find a close match in keywords
            match = self._find_best_match(word)

            if match:
                corrected_words.append(match)
                if match != word:
                    corrections[word] = match
            else:
                corrected_words.append(word)

        corrected_text = ' '.join(corrected_words)
        self.corrections = corrections

        return corrected_text, corrections

    def _find_best_match(self, word):
        """
        Find best matching keyword for a word.

        Args:
            word: Word to match

        Returns:
            Best matching keyword or None if no good match found
        """
        # Use rapidfuzz to find best match
        result = process.extractOne(
            word,
            ALL_KEYWORDS,
            scorer=fuzz.ratio,
            score_cutoff=70  # Minimum similarity threshold (70%)
        )

        if result:
            match, score, _ = result

            # Calculate approximate Levenshtein distance from similarity score
            # A rough approximation: distance ≈ len * (1 - score/100)
            approx_distance = len(word) * (1 - score / 100)

            if approx_distance <= self.max_distance:
                return match

        return None

    def get_corrections(self):
        """
        Get the corrections made during last correct_typos call.

        Returns:
            Dictionary mapping original_word -> corrected_word
        """
        return self.corrections

    def has_corrections(self):
        """
        Check if any corrections were made.

        Returns:
            True if corrections were made, False otherwise
        """
        return len(self.corrections) > 0
