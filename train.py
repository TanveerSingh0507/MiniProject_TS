import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def main():
    # Base path for backend files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    print("Loading actual fake news dataset...")
    url = "https://raw.githubusercontent.com/lutzhamel/fake-news/master/data/fake_or_real_news.csv"
    
    dataset_path = os.path.join(BASE_DIR, "dataset.csv")
    if not os.path.exists(dataset_path):
        print("Downloading dataset for the first time... This might take a moment.")
        df = pd.read_csv(url)
        df.to_csv(dataset_path, index=False)
    else:
        # Load the dataset
        df = pd.read_csv(dataset_path)

    print(f"Dataset shape: {df.shape}")

    # Check if 'text' and 'label' columns exist
    if 'text' not in df.columns or 'label' not in df.columns:
        print("Error: Dataset must contain 'text' and 'label' columns.")
        return

    # Drop any nulls just in case
    df = df.dropna(subset=['text', 'label'])

    # The dataset uses 'REAL' and 'FAKE' strings, map them to numeric
    # App.py expects 1 for Real, 0 for Fake
    if df['label'].dtype == object:
        df['label'] = df['label'].map({'REAL': 1, 'FAKE': 0})
        # Drop any failed mappings
        df = df.dropna(subset=['label'])
        df['label'] = df['label'].astype(int)

    # For the model, we use the text as feature and label as target
    X = df['text']
    y = df['label'] # 1 for Real, 0 for Fake

    print("Splitting dataset...")
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Initializing TfidfVectorizer...")
    # Initialize a TfidfVectorizer
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)

    # Fit and transform train set, transform test set
    tfidf_train = tfidf_vectorizer.fit_transform(x_train)
    tfidf_test = tfidf_vectorizer.transform(x_test)

    print("Training PassiveAggressiveClassifier...")
    # Initialize a PassiveAggressiveClassifier
    # We use a smaller C (loss regularization) to prevent overfitting slightly, defaults are fine though
    pac = PassiveAggressiveClassifier(max_iter=50)
    pac.fit(tfidf_train, y_train)

    print("Evaluating model...")
    # Predict on the test set and calculate accuracy
    y_pred = pac.predict(tfidf_test)
    score = accuracy_score(y_test, y_pred)
    print(f'Accuracy: {round(score*100,2)}%')
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=["Fake News", "Real News"]))

    # Save the model and vectorizer
    print("Saving model and vectorizer...")
    joblib.dump(pac, os.path.join(BASE_DIR, 'model.pkl'))
    joblib.dump(tfidf_vectorizer, os.path.join(BASE_DIR, 'vectorizer.pkl'))
    print("Training complete! Model saved as model.pkl and vectorizer saved as vectorizer.pkl.")

if __name__ == '__main__':
    main()