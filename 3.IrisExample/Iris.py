import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

CSV_name = "Iris.csv"


def show_confusion_matrix(confus_matrix):
    # Visualisering af testen
    sns.heatmap(confus_matrix, annot=True, cmap="Blues",
                xticklabels=["setosa", "versicolor", "virginica"],
                yticklabels=["setosa", "versicolor", "virginica"])
    plt.xlabel("Forudsagt klasse")
    plt.ylabel("Sand klasse")
    plt.show()

def show_decision_boundary(model, X_train, y_train, X_test, y_test, feature_kolonner, klasse_navne):
    # Gitter over feature-rummet
    x_min, x_max = X_train[:, 0].min() - 0.5, X_train[:, 0].max() + 0.5
    y_min, y_max = X_train[:, 1].min() - 0.5, X_train[:, 1].max() + 0.5
    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, 300),
        np.linspace(y_min, y_max, 300)
    )
    gitter = np.c_[xx.ravel(), yy.ravel()]
    Z = model.predict(gitter).reshape(xx.shape)

    plt.figure(figsize=(7, 5))
    plt.contourf(xx, yy, Z, alpha=0.3)

    for klasse_id, navn in enumerate(klasse_navne):
        plt.scatter(
            X_train[y_train == klasse_id, 0],
            X_train[y_train == klasse_id, 1],
            s=35, alpha=0.85, label=f"Træning – {navn}"
        )
        plt.scatter(
            X_test[y_test == klasse_id, 0],
            X_test[y_test == klasse_id, 1],
            s=60, alpha=0.95, edgecolors="k", label=f"Test – {navn}"
        )

    plt.xlabel(feature_kolonner[0])
    plt.ylabel(feature_kolonner[1])
    plt.title("Decision Boundary")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.show()

def Main():

    df = pd.read_csv(CSV_name)
    #print(df.head())

    #Fjerner Id kolonnen fra mit datasæt.
    if "Id" in df.columns:
        df = df.drop(columns=["Id"])

    #print(df.head())

    feature_kolonner = ["SepalLengthCm","SepalWidthCm"]
    #Giver kun tal fra kolonnerne
    X = df[feature_kolonner].values

    # Konvertere blomster art navne til tal setosa = 0,versicolor = 1,virginica = 2 dette kalde label encoding
    y_category = df["Species"].astype("category")
    y = y_category.cat.codes.values
    class_name = y_category.cat.categories.values

    #Her kan mapping ses i consolen
    print("Class-mapping (Tal -> Label):")
    for code, name in enumerate(class_name):
        print(f"{code}: {name}")
    print("\n")


    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    #Valg af model
    model = LogisticRegression(max_iter=200, random_state=42)

    #træner model
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    #Udregner modellen accuracy i forhold til at ramme rigtigt.
    model_accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {model_accuracy}")

    confus_matrix = confusion_matrix(y_test, y_pred)
    print(f"Confusion matrix (rækker = sande klasser, kolonner = forudsagte klasser):")
    print(confus_matrix,"\n")
    show_confusion_matrix(confus_matrix)

    report = classification_report(y_test, y_pred, target_names=class_name)
    print(report)

    show_decision_boundary(model, X_train, y_train, X_test, y_test, feature_kolonner, class_name)



if __name__ == "__main__":
    Main()
