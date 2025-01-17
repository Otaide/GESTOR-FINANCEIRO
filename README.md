# Gestão Financeira

Este é um aplicativo de gestão financeira desenvolvido em Python utilizando a biblioteca Tkinter para a interface gráfica e SQLite para o banco de dados. O aplicativo permite gerenciar movimentações financeiras, contas e exportar dados para CSV.

## Funcionalidades

- Adicionar, editar e excluir movimentações financeiras
- Adicionar e excluir contas
- Aplicar filtros para visualizar movimentações específicas
- Calcular o saldo total
- Exportar dados das movimentações para um arquivo CSV

## Tecnologias Utilizadas

- Python
- Tkinter
- SQLite
- tkcalendar

## Como Executar

1. Certifique-se de ter o Python instalado em sua máquina.
2. Instale as dependências necessárias:
    ```bash
    pip install tkcalendar
    ```
3. Execute o arquivo `main.py`:
    ```bash
    python main.py
    ```

## Estrutura do Projeto

- `main.py`: Arquivo principal contendo a lógica do aplicativo e a interface gráfica.
- `financeiro.db`: Banco de dados SQLite utilizado para armazenar as movimentações e contas.

## Capturas de Tela

### Tela Principal
![Tela Principal](screenshots/tela_principal.png)

### Tela de Filtros
![Tela de Filtros](screenshots/tela_filtros.png)

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
