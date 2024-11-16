import os
import joblib
from flask import Flask, render_template, request   # jsonify
from helpers import get_scaler
import numpy as np
import pandas as pd

# Configurações do Flask
app = Flask(__name__)

# Configs para pegar caminho absoluto do modelo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carregando o modelo
modelo_path = os.path.join(BASE_DIR, "modelo", "modelo_RL_bank.pkl")
modelo = joblib.load(modelo_path)

# normalizer -> "helpers.py"
scalers = get_scaler()

# Valores categóricos
categorical_features = {
    "person_gender": ["Masculino", "Feminino"],
    "person_education": ["High School", "Associate", "Bachelors", "Master", "Doctorate"],
    "person_home_ownership": ["RENT", "MORTGAGE", "OWN", "OTHER"],
    "loan_intent": ["EDUCATION", "MEDICAL", "VENTURE", "PERSONAL", "DEBTCONSOLIDATION"],
    "previous_loan_defaults_on_file": ["0", "1"],
}

# Mapeamentos de categorias para números
mapping_dicts = {}
for feature, categories in categorical_features.items():
    indices, unique_categories = pd.factorize(categories)           # pd.factorize -> atribui um índice único para cada categória
    
    # Dicionário de mapeamento para a feature atual
    feature_mapping = {category: idx for idx, category in enumerate(unique_categories)}
    mapping_dicts[feature] = feature_mapping

# Index
@app.route("/")
def formulario():
    return render_template("index.html")

# Resultado
@app.route("/result", methods=["POST"])
def prever():
    try:
        dados = request.form
        client_name = dados.get("client_name")


        # Converte e organiza os dados
        entrada = {
            "person_age": float(dados.get("person_age")),
            "person_income": float(dados.get("person_income")),
            "loan_amnt": float(dados.get("loan_amnt")),
            "loan_int_rate": float(dados.get("loan_int_rate")),
            "credit_score": float(dados.get("credit_score")),
        }

        # Lista para guardar os dados normalizados
        dados_normalizados = []
        # Itera sobre as colunas numéricas para normalizar os valores
        for col in entrada:
            valor_original = entrada[col]                                       # valor do form
            valor_transformado = scalers[col].transform([[valor_original]])     # normalização do valor do form
            valor_normalizado = valor_transformado[0][0]                        # extrai doarray
            dados_normalizados.append(valor_normalizado)                        # Entra na lista

        # Adição dos categóricos
        entrada_modelo = dados_normalizados + [
            mapping_dicts["person_gender"][dados.get("person_gender")],
            mapping_dicts["person_education"][dados.get("person_education")],
            mapping_dicts["person_home_ownership"][dados.get("person_home_ownership")],
            mapping_dicts["loan_intent"][dados.get("loan_intent")],
            float(dados.get("person_emp_exp")),
            float(dados.get("loan_percent_income")),
            float(dados.get("cb_person_cred_hist_length")),
            mapping_dicts["previous_loan_defaults_on_file"][dados.get("previous_loan_defaults_on_file")],
        ]

        # Usa o modelo .pkl para realizar a predição
        previsao = modelo.predict([entrada_modelo])

        # Resultado da previsão (int)
        resultado = int(previsao[0])

        # Resultado
        if (resultado == 1):
            mensagem = "Empréstimo Aprovado!"
            cor = "success"                         # cor verde (bootstrap)
        else:
            mensagem = "Empréstimo Negado!"
            cor = "danger"                          # cor vermelha (bootstrap)
        return render_template("result.html", client_name=client_name, mensagem=mensagem, cor=cor)
    except Exception as e:
        return render_template("result.html", client_name="Erro. Tente novamente", mensagem=str(e), cor="danger")

if __name__ == "__main__":
    app.run(debug = True)

