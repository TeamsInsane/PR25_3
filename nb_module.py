import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import CategoricalNB

def compute_naive_bayes_table(modelData):
    df = modelData[["VrstaCesteNaselja", "KlasifikacijaNesrece"]].dropna()

    le_road = LabelEncoder()
    le_severity = LabelEncoder()

    X = le_road.fit_transform(df["VrstaCesteNaselja"]).reshape(-1, 1)
    y = le_severity.fit_transform(df["KlasifikacijaNesrece"])

    model = CategoricalNB()
    model.fit(X, y)

    probs = model.predict_proba([[i] for i in range(len(le_road.classes_))])
  
    probs_df = pd.DataFrame(
        probs,
        index=le_road.classes_,
        columns=le_severity.classes_
    )

    return probs_df
