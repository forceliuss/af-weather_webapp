# Weather Data Pipeline - ETL com Airflow, Supabase e Streamlit

Este projeto demonstra a construção de um pipeline ETL completo para ingestão e transformação de dados meteorológicos, utilizando Apache Airflow, Supabase e Streamlit para visualização.

## 📺 Vídeo do Projeto

Este repositório está vinculado ao seguinte vídeo do YouTube:

**Título:** Construindo um pipeline de ingestão e transformação de dados | Airflow + Supabase + Streamlit  
**Link:** https://youtu.be/L7CGbQmPElQ

## 📋 Visão Geral

Este projeto implementa um pipeline de dados end-to-end que:

1. **Extrai** dados meteorológicos da API do OpenWeatherMap para a cidade do Rio de Janeiro
2. **Transforma** os dados (normalização, conversão de unidades, enriquecimento)
3. **Carrega** os dados transformados no Supabase (PostgreSQL)
4. **Visualiza** os dados através de um dashboard interativo em Streamlit

## 🏗️ Arquitetura

- **Apache Airflow**: Orquestração do pipeline ETL
- **Astronomer**: Ambiente de desenvolvimento e execução do Airflow
- **OpenWeatherMap API**: Fonte de dados meteorológicos
- **Supabase**: Banco de dados PostgreSQL na nuvem
- **Streamlit**: Dashboard web para visualização dos dados

## 📁 Estrutura do Projeto

```
.
├── dags/
│   └── weather_pipeline.py    # DAG do Airflow com as tarefas ETL
├── app.py                      # Aplicação Streamlit para visualização
├── requirements.txt            # Dependências Python do projeto
├── Dockerfile                  # Imagem Docker do Astro Runtime
├── airflow_settings.yaml      # Configurações locais do Airflow
└── README.md                  # Este arquivo
```

## 🔧 Pré-requisitos

- Python 3.8+
- Docker e Docker Compose
- Astronomer CLI instalado
- Conta no OpenWeatherMap (API Key gratuita)
- Projeto no Supabase configurado

## 🚀 Configuração

### 1. Instalar Astronomer CLI

Siga as instruções em: https://www.astronomer.io/docs/astro/cli/install-cli

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# OpenWeatherMap API
OPENWEATHER_API_KEY=sua_api_key_aqui

# Supabase Database
DB_HOST=seu_host_supabase
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_PORT=5432
DB_DBNAME=postgres
```

### 3. Iniciar o Ambiente Airflow

```bash
astro dev start
```

Este comando irá iniciar 4 containers Docker:

- **Postgres**: Banco de dados de metadados do Airflow
- **Webserver**: Interface web do Airflow (porta 8080)
- **Scheduler**: Componente que monitora e dispara as tarefas
- **Triggerer**: Componente responsável por tarefas deferidas

### 4. Acessar o Airflow UI

Acesse http://localhost:8080/ e faça login com:

- **Username:** `admin`
- **Password:** `admin`

### 5. Executar o Streamlit App

Em um terminal separado:

```bash
streamlit run app.py
```

O dashboard estará disponível em http://localhost:8501

## 📊 Pipeline ETL

O DAG `weather_pipeline` executa as seguintes tarefas:

1. **Extract**: Busca dados meteorológicos da API OpenWeatherMap
2. **Transform**:
   - Normaliza dados aninhados (weather, sys, etc.)
   - Converte temperaturas de Kelvin para Celsius
   - Adiciona timestamp de coleta
   - Estrutura dados para o schema do banco
3. **Load**: Insere dados transformados no Supabase

O pipeline é executado a cada 2 minutos por padrão.

## 🗄️ Schema do Banco de Dados

Os dados são armazenados na tabela `weather.weather_data` com os seguintes campos principais:

- Informações básicas: `city`, `collection_timestamp`
- Temperaturas: `temperature_c`, `thermal_sensation_c`, `temp_min_c`, `temp_max_c`
- Condições: `humidity`, `pressure`, `wind_speed`, `wind_direction`
- Localização: `latitude`, `longitude`
- Clima: `weather_main`, `weather_description`, `weather_icon`
- Sistema: `sys_country`, `sys_sunrise`, `sys_sunset`

## 📚 Recursos e Documentação

### Tutoriais e Guias

- [PT] Instalação Python - https://www.youtube.com/watch?v=-M4pMd2yQOM
- [EN] Ambiente Conda - https://www.youtube.com/watch?v=qI3P7zMMsgY
- [EN] Configuração Supabase - https://www.youtube.com/watch?v=zBZgdTb-dns
- [EN] Começando com Astronomer - https://www.youtube.com/watch?v=Gvw1QZ4oUiw

### Documentação Oficial

- [Anaconda Guide](https://www.anaconda.com/docs/getting-started/anaconda/install)
- [Astronomer Documentation](https://www.astronomer.io/docs/home/astronomer-documentation)
- [OpenWeatherMap API](https://openweathermap.org/current)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🛠️ Tecnologias Utilizadas

- **Apache Airflow**: Orquestração de workflows
- **Astronomer**: Runtime e ferramentas para Airflow
- **Python**: Linguagem de programação
- **Pandas**: Manipulação de dados
- **SQLAlchemy**: ORM e conexão com banco de dados
- **Streamlit**: Framework para aplicações web
- **Plotly**: Visualizações interativas
- **Supabase**: Banco de dados PostgreSQL gerenciado

## 📝 Notas

- O pipeline coleta dados para a cidade do Rio de Janeiro por padrão
- Os dados são armazenados em um schema separado (`weather`) no Supabase
- O dashboard Streamlit atualiza automaticamente a cada 2 minutos
- Certifique-se de ter uma API Key válida do OpenWeatherMap

## 🤝 Contribuindo

Este é um projeto educacional vinculado a um vídeo do YouTube. Sinta-se à vontade para fazer fork e adaptar para suas necessidades!

## 📧 Contato

Para conteúdo mais aprofundado sobre o mundo de dados:

- **Substack**: https://substack.com/@forcelius
- **Medium**: https://medium.com/@forceliuss

---

**Soundtracks:** Epidemic Sound - https://share.epidemicsound.com/82aru1
