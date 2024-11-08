# PC DESEMPENHO IOT

## Descrição
PC DESEMPENHO IOT é uma aplicação executável em Python que monitora o uso de CPU, RAM e Ethernet do seu computador, enviando essas informações para um broker MQTT de sua escolha. A aplicação possui uma interface gráfica que exibe logs das informações enviadas e permite receber mensagens e alterar configurações de reporte através de tópicos de subscrição.

## Funcionalidades
- Monitoramento em tempo real de CPU, RAM e Ethernet
- Envio de dados para broker MQTT configurável
- Interface gráfica com exibição de logs
- Recebimento de mensagens via MQTT
- Alteração dinâmica das configurações de reporte

## Requisitos
- Python 3.7+
- Bibliotecas: paho-mqtt, psutil, tkinter

## Instalação
1. Clone o repositório:
    ```sh
    git clone https://github.com/edersonvieira/pc-desempenho-iot.git
    ```
2. Navegue até o diretório do projeto:
    ```sh
    cd pc-desempenho-iot
    ```
3. Instale as dependências:
    ```sh
    pip install -r requirements.txt
    ```

## Uso
1. Execute o arquivo principal:
    ```sh
    python main.py
    ```
2. Na interface gráfica, configure o endereço do broker MQTT e os tópicos de publicação/subscrição.
3. Clique em "Iniciar Monitoramento" para começar a enviar dados.
4. Você pode usar o executável em dist, é necessário manter ico para trayicon funcionar.

## Configuração
- Broker MQTT: Insira o endereço IP ou hostname do seu broker MQTT.
- Tópico de Publicação: Defina o tópico para onde os dados serão enviados.
- Tópico de Subscrição: Defina o tópico para receber mensagens e alterações de configuração.

## Logs
A interface exibirá logs em tempo real das informações enviadas e recebidas.

## Alteração de Configurações
Envie mensagens para o tópico de subscrição para alterar as configurações de reporte, como intervalo de envio ou tipos de dados monitorados.

## Contribuições
Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças propostas ou envie um pull request.
