import streamlit as st
import pandas as pd
from io import StringIO

# Função para sugerir transformações básicas
def suggest_transformations(df):
    suggestions = {}
    for col in df.columns:
        dtype = df[col].dtype
        
        # Sugere conversão de strings para caixa baixa
        if dtype == 'object':
            suggestions[col] = "Converter strings para minúsculas"
        
        # Sugere tratamento de valores misturados
        if dtype == 'object':
            mixed_values = df[col].apply(lambda x: pd.to_numeric(x, errors='coerce')).isnull().sum()
            if mixed_values > 0:
                suggestions[col] = "Valores misturados. Sugestão: Remover valores ruidosos ou converter para numérico."
        
        # Sugere tratamento de valores ausentes
        null_values = df[col].isnull().sum()
        if null_values > 0:
            suggestions[col] = f"{null_values} valores ausentes. Escolha ações: Imputar valores ou Deletar linhas."
    
    return suggestions

# Função para aplicar as transformações escolhidas
def apply_transformations(df, choices):
    df_copy = df.copy()
    
    for col, actions in choices.items():
        for action in actions:
            if action == "Converter strings para minúsculas":
                if df_copy[col].dtype == 'object':
                    df_copy[col] = df_copy[col].str.lower()
            
            if action == "Remover valores ruidosos":
                if df_copy[col].dtype == 'object':
                    # Converter valores não numéricos para NaN
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                    df_copy.dropna(subset=[col], inplace=True)
            
            if action == "Converter para numérico":
                # Converter valores para numérico, substituindo valores não convertíveis por NaN
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            
            if action == "Imputar pela média":
                if df_copy[col].dtype in ['float64', 'int64']:
                    df_copy[col].fillna(df_copy[col].mean(), inplace=True)
                else:
                    st.warning(f"Não é possível imputar média na coluna '{col}', pois não é numérica.")
            
            if action == "Imputar pela mediana":
                if df_copy[col].dtype in ['float64', 'int64']:
                    df_copy[col].fillna(df_copy[col].median(), inplace=True)
                else:
                    st.warning(f"Não é possível imputar mediana na coluna '{col}', pois não é numérica.")
            
            if action == "Deletar linhas":
                df_copy.dropna(subset=[col], inplace=True)
            
            if action == "Deletar coluna":
                if col in df_copy.columns:
                    df_copy.drop(columns=[col], inplace=True)
            
            if action == "Normalizar":
                if df_copy[col].dtype in ['float64', 'int64']:
                    df_copy[col] = (df_copy[col] - df_copy[col].min()) / (df_copy[col].max() - df_copy[col].min())
                else:
                    st.warning(f"Não é possível normalizar a coluna '{col}', pois não é numérica.")
            
            if action == "Padronizar":
                if df_copy[col].dtype in ['float64', 'int64']:
                    df_copy[col] = (df_copy[col] - df_copy[col].mean()) / df_copy[col].std()
                else:
                    st.warning(f"Não é possível padronizar a coluna '{col}', pois não é numérica.")
            
            if action == "Substituir valores":
                if df_copy[col].dtype == 'object':
                    df_copy[col].replace(to_replace=['NaN', 'NA'], value='Desconhecido', inplace=True)
    
    return df_copy

# Interface do Streamlit
st.title("Feature Store - Sugestão e Transformação de Dados")

# Upload do CSV
uploaded_file = st.file_uploader("Envie seu arquivo CSV", type="csv")

if uploaded_file is not None:
    # Ler o arquivo CSV
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)
    
    # Etapa 1: Mostrar dados brutos
    st.write("### Etapa 1: Dados Brutos")
    st.dataframe(df)
    
    # Etapa 2: Sugestão de transformações
    st.write("### Etapa 2: Sugestões de Transformações")
    suggestions = suggest_transformations(df)
    
    # Guardar escolhas do usuário
    choices = {}
    
    for col, suggestion in suggestions.items():
        st.markdown(f"**Coluna:** `{col}`")
        st.markdown(f"**Sugestão:** {suggestion}")
        
        # Seleção de ações múltiplas com multiselect
        actions = st.multiselect(
            f"Escolha ações para a coluna '{col}'",
            ["Converter strings para minúsculas", "Remover valores ruidosos", "Converter para numérico",
             "Imputar pela média", "Imputar pela mediana", "Deletar linhas", "Deletar coluna",
             "Normalizar", "Padronizar", "Substituir valores"],
            key=f"multiselect_{col}"
        )
        
        if actions:
            choices[col] = actions
        
        # Mostrar estado da coluna antes e depois da transformação após a seleção
        if actions:
            df_transformed = apply_transformations(df, {col: actions})
            
            # Verificar se a coluna ainda existe antes de tentar exibir
            if col in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Antes (Coluna `{col}`):**")
                    st.dataframe(df[[col]])
                with col2:
                    st.write(f"**Depois (Coluna `{col}`):**")
                    if col in df_transformed.columns:
                        st.dataframe(df_transformed[[col]])
                    else:
                        st.write(f"A coluna `{col}` foi removida.")
    
    # Aplicar transformações e mostrar os resultados finais
    if st.button("Aplicar Todas Sugestões"):
        with st.spinner('Aplicando transformações...'):
            df_transformed = apply_transformations(df, choices)
        
        st.success("Transformações aplicadas!")
        
        # Etapa 3: Mostrar dados transformados
        st.write("### Etapa 3: Dados Transformados")
        st.dataframe(df_transformed)
        
        # Download do CSV processado
        csv = df_transformed.to_csv(index=False)
        st.download_button(
            label="Baixar CSV Processado", 
            data=csv, 
            file_name="processed_features.csv", 
            mime="text/csv"
        )
