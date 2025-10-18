# simple_utils.py - A tiny utility library

def reverse_string(text):
    """Reverses the characters in a string."""
    return text[::-1]

def count_words(sentence):
    """
    Count the number of whitespace-separated words in a sentence.
    
    Parameters:
        sentence (str): Input text; words are sequences separated by any whitespace.
    
    Returns:
        int: The number of words (0 if the sentence is empty or contains only whitespace).
    """
    return len(sentence.split())

def celsius_to_fahrenheit(celsius):
    """
    Convert a temperature from degrees Celsius to degrees Fahrenheit.
    
    Parameters:
        celsius (float): Temperature in degrees Celsius.
    
    Returns:
        float: Temperature in degrees Fahrenheit.
    """
    return (celsius * 9/5) + 32