from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
import pandas as pd

def train_models(data):
    modelData = data.copy()
    modelData["UraPN"] = modelData.dropna(subset=['UraPN'])['UraPN'].astype(int)
    modelData['DatumPN'] = pd.to_datetime(modelData['DatumPN'], dayfirst=True, errors='coerce')
    modelData['DanVTednu'] = modelData['DatumPN'].dt.dayofweek

    features = [
        "UraPN", 
        "DanVTednu", 
        "VrstaCesteNaselja",
        "StanjeVozisca",
        "TipNesrece",
        "VremenskeOkoliscine",
        "VrednostAlkotesta",
    ]

    target = "KlasifikacijaNesrece"
    modelData = modelData.dropna(subset=[target])

    X = modelData[features].copy()
    y = modelData[target].copy()

    categorical = X.select_dtypes(include="object").columns
    label_encoders = {}

    for col in categorical:
        modelData[col] = modelData[col].astype(str).str.upper()
        le = LabelEncoder()
        X[col] = le.fit_transform(modelData[col])
        label_encoders[col] = le

    y_encoder = LabelEncoder()
    y = y_encoder.fit_transform(y.astype(str))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "DecisionTree": DecisionTreeClassifier(),
        "XGBoost": XGBClassifier(eval_metric="mlogloss")
    }

    for name, model in models.items():
        model.fit(X_train, y_train)

    return models, label_encoders, y_encoder
