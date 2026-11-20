# Fleet Intelligence

**Inteligência e otimização financeira para gestão de frotas.**

O Fleet Intelligence é uma proposta de plataforma para apoiar gestores de frota na consolidação de despesas, identificação de possíveis ineficiências e estimativa de oportunidades de economia.

O projeto faz parte do Enterprise Challenge da FIAP, em parceria com a Sem Parar Empresas, e tem como foco as necessidades do **Gestor de Frota**.

## 1. Problema

As informações financeiras e operacionais de uma frota podem estar distribuídas em diferentes planilhas, documentos e sistemas. Essa fragmentação dificulta a análise dos custos, a identificação de gastos fora do padrão e a tomada de decisões.

O Fleet Intelligence propõe centralizar essas informações e transformá-las em indicadores, diagnósticos e recomendações práticas.

## 2. Objetivo

Desenvolver uma solução que permita ao Gestor de Frota:

- Importar dados de despesas em diferentes formatos.
- Visualizar os custos consolidados por categoria, veículo e período.
- Identificar possíveis anomalias e ineficiências.
- Receber recomendações priorizadas com estimativas de economia em reais.
- Obter um diagnóstico inicial mesmo quando os dados disponíveis estiverem incompletos.

## 3. Histórias de usuário

As histórias abaixo foram elaboradas a partir das necessidades do Gestor de Frota identificadas no desafio.

| ID | História de usuário | Resultado esperado |
|---|---|---|
| US01 | Como Gestor de Frota, quero importar despesas de planilhas e documentos para centralizar os custos da operação. | Dados extraídos e organizados em uma estrutura padronizada. |
| US02 | Como Gestor de Frota, quero visualizar os custos por categoria, veículo e período para acompanhar os gastos da frota. | Indicadores e relatórios consolidados. |
| US03 | Como Gestor de Frota, quero identificar despesas fora dos padrões esperados para investigar possíveis desperdícios. | Alertas e apontamentos de possíveis anomalias. |
| US04 | Como Gestor de Frota, quero receber recomendações práticas com estimativas de economia para priorizar ações. | Recomendações acompanhadas de valores estimados e justificativas. |
| US05 | Como Gestor de Frota, quero receber um diagnóstico mesmo com dados incompletos e saber quais informações estão faltando. | Diagnóstico parcial com indicação das limitações dos dados. |

## 4. Solução proposta

A solução será organizada em etapas:

1. **Ingestão:** recebimento de planilhas, arquivos e outras fontes de dados.
2. **Extração e validação:** leitura, padronização e verificação das informações.
3. **Consolidação:** organização dos registros por veículo, categoria e período.
4. **Análise:** cálculo de indicadores e identificação de possíveis anomalias.
5. **Diagnóstico:** interpretação dos resultados e estimativa de oportunidades de economia.
6. **Apresentação:** disponibilização dos resultados em dashboards e relatórios.

As estimativas financeiras serão calculadas por regras determinísticas em Python. A IA generativa poderá auxiliar na explicação dos resultados e na apresentação das recomendações, mas não deverá inventar valores ou substituir os cálculos financeiros.

## 5. Tecnologias propostas

| Tecnologia | Aplicação |
|---|---|
| Python | Linguagem principal do projeto. |
| Pandas e NumPy | Tratamento, padronização e análise dos dados. |
| OCR | Extração de informações de documentos e imagens. |
| Scikit-learn | Identificação de possíveis anomalias nos dados. |
| FastAPI | Desenvolvimento da camada de API. |
| PostgreSQL | Armazenamento dos dados estruturados. |
| Streamlit | Desenvolvimento da interface da aplicação. |
| Plotly | Construção de gráficos e visualizações. |
| IA generativa | Explicação dos diagnósticos e apoio às recomendações. |

As tecnologias representam a arquitetura proposta e poderão ser ajustadas durante a implementação.

## 6. Dataset de desenvolvimento

Para iniciar o desenvolvimento e validar a lógica de análise, foi elaborado um dataset fictício com despesas de uma frota simulada.

**Características do dataset:**

- 194 registros de despesas.
- 12 veículos de diferentes categorias.
- Período de referência: janeiro a março de 2026.
- Categorias: combustível, manutenção, pedágio, multas, impostos e outras despesas.
- Registros de consumo e distância para análises de eficiência de combustível.
- Inconsistências e situações atípicas simuladas para testar as validações e os diagnósticos.

Os dados são exclusivamente fictícios e destinados a fins acadêmicos. Não representam uma frota real nem constituem referência de mercado.

### Arquivos

- `fleet_intelligence_dataset.csv`: dataset em formato CSV.
- `fleet_intelligence_dataset_e_dicionario.xlsx`: planilha com dataset, dicionário de dados e premissas.

## 7. Critérios de validação dos dados

Antes de realizar análises, os registros deverão passar por verificações de estrutura, integridade, consistência e qualidade.

As validações serão classificadas em:

- **Erro:** registro inválido ou inconsistente que não deve seguir para os cálculos afetados.
- **Alerta:** informação suspeita ou incompleta que exige atenção, mas não necessariamente impede todo o processamento.
- **Informativo:** condição que deve ser apresentada ao usuário, sem caracterizar erro.

Os critérios detalhados estão descritos em `CRITERIOS_VALIDACAO_DATASET.md`.

## 8. Indicadores e análises previstos

A plataforma deverá permitir o acompanhamento de indicadores como:

- Custo total da frota.
- Despesas por categoria.
- Despesas por veículo e período.
- Custo por quilômetro.
- Consumo de combustível em litros por 100 km.
- Variação dos custos ao longo do tempo.
- Despesas e indicadores fora do padrão histórico.

As comparações deverão considerar veículos ou grupos comparáveis. Uma anomalia representa um sinal para investigação, não uma confirmação automática de desperdício.

## 9. Estimativa de economia

A estimativa de economia deverá utilizar dados disponíveis e premissas explícitas.

Para combustível, por exemplo, será possível comparar o consumo observado com uma referência histórica do próprio veículo ou de um grupo comparável.

A estimativa deverá apresentar:

- Consumo observado.
- Consumo de referência.
- Diferença identificada.
- Preço unitário utilizado.
- Economia potencial estimada.
- Premissas e limitações do cálculo.

Economia potencial não significa economia realizada ou garantida.

## 10. Tratamento de dados incompletos

A ausência de uma informação não deverá ser preenchida com valores inventados.

Quando faltarem dados necessários para determinado indicador, a plataforma deverá:

- Identificar os campos ausentes.
- Informar quais análises ficaram indisponíveis.
- Apresentar os indicadores que ainda podem ser calculados.
- Orientar o usuário sobre quais informações precisam ser fornecidas.

## 11. Planejamento das Sprints

O desenvolvimento do Fleet Intelligence será dividido em quatro Sprints. A primeira etapa contempla o planejamento da solução; as três seguintes serão destinadas à implementação e integração das funcionalidades.

### Sprint 1 — Planejamento e definição da solução

**Objetivo:** estruturar a proposta técnica e definir como a solução será desenvolvida.

Atividades:
- Compreender o problema e definir o escopo do projeto.
- Selecionar e documentar as histórias de usuário.
- Definir a arquitetura inicial da solução.
- Identificar os dados necessários para as análises.
- Criar o dataset fictício e seu dicionário de dados.
- Definir os critérios de validação.
- Planejar as etapas de desenvolvimento.

**Entregáveis:**
- README e documentação inicial.
- Histórias de usuário.
- Diagrama de arquitetura.
- Dataset e dicionário de dados.
- Critérios de validação.
- Planejamento de desenvolvimento.

### Sprint 2 — Ingestão, validação e indicadores financeiros

**Objetivo:** desenvolver a base de processamento dos dados e os primeiros indicadores financeiros.

Atividades:
- Implementar a leitura de arquivos CSV e Excel.
- Desenvolver o módulo de validação dos dados.
- Identificar registros inválidos, incompletos e possíveis duplicidades.
- Padronizar datas, categorias e valores.
- Consolidar despesas por veículo, categoria e período.
- Calcular custo total, custo por quilômetro e indicadores de consumo.
- Criar relatórios de qualidade dos dados.

**Entregáveis:**
- Módulo de ingestão.
- Módulo de validação.
- Pipeline de tratamento e consolidação.
- Indicadores financeiros iniciais.
- Relatório de qualidade dos dados.

**Critério de conclusão:** os dados devem ser importados, validados e processados corretamente, com indicadores financeiros conferidos.

### Sprint 3 — Inteligência, diagnóstico e recomendações

**Objetivo:** implementar a identificação de possíveis ineficiências e transformar os resultados em oportunidades de economia.

Atividades:
- Desenvolver regras para identificação de variações relevantes.
- Implementar detecção de anomalias utilizando Scikit-learn e Isolation Forest.
- Comparar os resultados do modelo com as regras determinísticas.
- Identificar despesas e consumos fora dos padrões esperados.
- Desenvolver o motor de diagnóstico.
- Calcular oportunidades potenciais de economia.
- Criar recomendações práticas e priorizadas.
- Considerar a qualidade e a disponibilidade dos dados na geração dos diagnósticos.

**Entregáveis:**
- Módulo de detecção de anomalias.
- Resultados da análise e validação do modelo.
- Motor de diagnóstico.
- Cálculos de economia potencial.
- Módulo de recomendações.

**Critério de conclusão:** o sistema deverá identificar situações atípicas, apresentar justificativas e calcular oportunidades de economia com premissas explícitas.

### Sprint 4 — Interface, integração e finalização

**Objetivo:** integrar os módulos desenvolvidos e disponibilizar um protótipo funcional para o Gestor de Frota.

Atividades:
- Desenvolver a interface utilizando Streamlit.
- Criar a aba de monitoramento financeiro.
- Criar a aba de validação e análise da IA.
- Apresentar indicadores, alertas, diagnósticos e recomendações.
- Permitir o carregamento de novos arquivos.
- Integrar ingestão, validação, processamento e análise.
- Implementar tratamento de erros.
- Realizar testes do fluxo completo.
- Finalizar documentação e apresentação do projeto.

**Entregáveis:**
- Aplicação integrada.
- Dashboard de monitoramento.
- Interface de validação e análise da IA.
- Fluxo de importação e processamento.
- Documentação técnica atualizada.
- Demonstração do protótipo funcional.

**Critério de conclusão:** o Gestor de Frota deverá conseguir importar dados, visualizar indicadores, identificar possíveis anomalias e consultar diagnósticos e recomendações na aplicação.

## 12. Estrutura prevista do projeto

A organização inicial dos arquivos poderá seguir esta estrutura:

```text
fleet-intelligence/
├── README.md
├── CRITERIOS_VALIDACAO_DATASET.md
├── data/
│   ├── fleet_intelligence_dataset.csv
│   └── fleet_intelligence_dataset_e_dicionario.xlsx
├── docs/
│   ├── arquitetura.md
│   └── historias_de_usuario.md
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── processing/
│   └── analysis/
└── app/
```

A estrutura é uma proposta inicial e será ampliada conforme a implementação evoluir.

## 13. Limitações e premissas

- O dataset atual é pequeno e fictício.
- Os dados simulados permitem testar o fluxo, mas não comprovam desempenho em uma operação real.
- Modelos de detecção de anomalias dependem da qualidade e da quantidade dos dados.
- Comparações externas só deverão ser apresentadas quando houver referências confiáveis e documentadas.
- Recomendações financeiras deverão apresentar suas premissas e limitações.
- As estimativas de economia representam oportunidades potenciais, não resultados garantidos.

## 14. Próximos passos

A próxima etapa de desenvolvimento será a Sprint 2, com foco na ingestão, validação, tratamento e consolidação dos dados.

A prioridade será construir uma base confiável de processamento antes de avançar para os modelos de Machine Learning e os diagnósticos financeiros.

---

**Projeto acadêmico — FIAP | Enterprise Challenge | Sem Parar Empresas**