import sys
import psutil
import json
import paho.mqtt.client as mqtt
import time
import logging
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                             QPushButton, QTextEdit, QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject

# Configuração de logging
logging.basicConfig(filename='performance.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MonitoramentoDesempenho(QObject):
    sinal_log = pyqtSignal(str)

    def __init__(self, broker, topico_pub, topico_sub, usuario, senha):
        super().__init__()
        self.broker = broker
        self.topico_pub = topico_pub
        self.topico_sub = topico_sub
        self.usuario = usuario
        self.senha = senha
        self.tempo_espera = 60
        self.executar = True
        self.cliente = mqtt.Client()
        self.cliente.username_pw_set(self.usuario, self.senha)
        self.cliente.on_message = self.on_message

    def conectar(self):
        """Conectar ao broker MQTT."""
        try:
            self.cliente.connect(self.broker)
            self.cliente.subscribe(self.topico_sub)
            self.cliente.loop_start()
            self.sinal_log.emit("Conectado ao broker MQTT.")
        except Exception as e:
            logging.error(f"Erro ao conectar ao broker: {e}")
            self.sinal_log.emit(f"Erro ao conectar ao broker: {e}")

    def desconectar(self):
        """Desconectar do broker MQTT."""
        self.cliente.loop_stop()
        self.cliente.disconnect()
        self.sinal_log.emit("Desconectado do broker MQTT.")

    def coletar_informacoes(self):
        """Coletar estatísticas de uso de CPU, memória, disco e rede."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memoria = psutil.virtual_memory()
            disco = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()

            informacoes = {
                "cpu_percent": cpu_percent,
                "memoria_usada_gb": memoria.used / (1024 ** 3),
                "memoria_percent": memoria.percent,
                "disco_usado_gb": disco.used / (1024 ** 3),
                "disco_percent": disco.percent,
                "bytes_enviados": net_io.bytes_sent,
                "bytes_recebidos": net_io.bytes_recv,
            }
            return informacoes
        except Exception as e:
            logging.error(f"Erro ao coletar informações do sistema: {e}")
            self.sinal_log.emit(f"Erro ao coletar informações do sistema: {e}")
            return {}

    def enviar_mqtt(self, informacoes):
        """Enviar informações coletadas para o broker MQTT."""
        try:
            mensagem = json.dumps(informacoes)
            self.cliente.publish(self.topico_pub, mensagem)
            self.sinal_log.emit(f"Informações enviadas: {informacoes}")
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem MQTT: {e}")
            self.sinal_log.emit(f"Erro ao enviar mensagem MQTT: {e}")

    def on_message(self, client, userdata, msg):
        """Manipular mensagens recebidas do tópico inscrito."""
        try:
            mensagem = json.loads(msg.payload.decode())
            self.sinal_log.emit(f"Informações recebidas: {mensagem}")

            if 'tempo_espera' in mensagem:
                self.tempo_espera = mensagem['tempo_espera']
                self.sinal_log.emit(f"Tempo de espera alterado para: {self.tempo_espera} segundos.")
            if 'comunicacao' in mensagem:
                self.executar = bool(mensagem['comunicacao'])
                estado = "iniciado" if self.executar else "parado"
                self.sinal_log.emit(f"Envio de informações {estado}.")
            if 'mensagem' in mensagem:
                self.sinal_log.emit(f"Mensagem: {mensagem['mensagem']}")

        except json.JSONDecodeError as e:
            self.sinal_log.emit(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            self.sinal_log.emit(f"Erro inesperado: {e}")

    def executar_monitoramento(self):
        """Loop principal para monitorar o desempenho do sistema."""
        bytes_enviados_anterior = psutil.net_io_counters().bytes_sent
        bytes_recebidos_anterior = psutil.net_io_counters().bytes_recv

        while self.executar:
            informacoes = self.coletar_informacoes()
            if informacoes:
                bytes_enviados_atual = psutil.net_io_counters().bytes_sent
                bytes_recebidos_atual = psutil.net_io_counters().bytes_recv

                informacoes['send_kbps'] = (bytes_enviados_atual - bytes_enviados_anterior) * 8 / 1024
                informacoes['receive_kbps'] = (bytes_recebidos_atual - bytes_recebidos_anterior) * 8 / 1024

                bytes_enviados_anterior = bytes_enviados_atual
                bytes_recebidos_anterior = bytes_recebidos_atual

                self.enviar_mqtt(informacoes)

            time.sleep(self.tempo_espera)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.monitor = None
        self.thread = None
        self.tray_icon = None
        self.mensagens_log = set()
        self.carregar_ultimos_inputs()

    def initUI(self):
        """Inicializar a interface do usuário."""
        self.setWindowTitle('PC Desempenho')
        self.setWindowIcon(QIcon('icon.svg'))
        layout = QVBoxLayout()

        # Campos de entrada para detalhes do broker MQTT
        self.broker_input = self.criar_input('Broker MQTT')
        self.topico_pub_input = self.criar_input('Tópico de Publicação')
        self.topico_sub_input = self.criar_input('Tópico de Inscrição')
        self.usuario_input = self.criar_input('Usuário')
        self.senha_input = self.criar_input('Senha', True)

        # Botões para iniciar e parar o monitoramento
        self.botao_iniciar = QPushButton('Iniciar Monitoramento', self)
        self.botao_iniciar.clicked.connect(self.iniciar_monitoramento)
        layout.addWidget(self.botao_iniciar)

        self.botao_parar = QPushButton('Parar Monitoramento', self)
        self.botao_parar.clicked.connect(self.parar_monitoramento)
        layout.addWidget(self.botao_parar)

        # Área de log para exibir mensagens
        self.area_log = QTextEdit(self)
        self.area_log.setReadOnly(True)
        layout.addWidget(self.area_log)

        layout.addWidget(self.broker_input)
        layout.addWidget(self.topico_pub_input)
        layout.addWidget(self.topico_sub_input)
        layout.addWidget(self.usuario_input)
        layout.addWidget(self.senha_input)

        self.setLayout(layout)
        self.criar_tray_icon()

    def criar_input(self, placeholder, is_password=False):
        """Criar um campo de entrada."""
        input_field = QLineEdit(self)
        input_field.setPlaceholderText(placeholder)
        if is_password:
            input_field.setEchoMode(QLineEdit.Password)
        return input_field

    def criar_tray_icon(self):
        """Criar e configurar o ícone da bandeja do sistema."""
        self.tray_icon = QSystemTrayIcon(QIcon('icon.svg'), self)
        self.tray_icon.setToolTip('PC Desempenho')

        # Criar o menu de contexto
        menu = QMenu()
        acao_abrir = QAction("Abrir", self)
        acao_abrir.triggered.connect(self.show)
        menu.addAction(acao_abrir)

        acao_sair = QAction("Sair", self)
        acao_sair.triggered.connect(self.sair_aplicacao)
        menu.addAction(acao_sair)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        # Conectar o evento de ativação do ícone da bandeja
        self.tray_icon.activated.connect(self.tray_icon_ativado)

    def tray_icon_ativado(self, motivo):
        """Manipular ações quando o ícone da bandeja é ativado."""
        if motivo == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def iniciar_monitoramento(self):
        """Iniciar o processo de PC Desempenho."""
        broker = self.broker_input.text().strip()
        topico_pub = self.topico_pub_input.text().strip()
        topico_sub = self.topico_sub_input.text().strip()
        usuario = self.usuario_input.text().strip()
        senha = self.senha_input.text().strip()

        if not broker or not topico_pub or not topico_sub:
            QMessageBox.warning(self, "Erro de Entrada", "Por favor, preencha todos os campos.")
            return

        self.monitor = MonitoramentoDesempenho(broker, topico_pub, topico_sub, usuario, senha)
        self.monitor.sinal_log.connect(self.log_callback)

        self.monitor.conectar()
        self.area_log.append("Monitoramento iniciado...")
        self.monitor.executar = True

        self.thread = threading.Thread(target=self.monitor.executar_monitoramento, daemon=True)
        self.thread.start()

        self.salvar_ultimos_inputs(broker, topico_pub, topico_sub, usuario, senha)

    def parar_monitoramento(self):
        """Parar o processo de PC Desempenho."""
        if self.monitor:
            self.monitor.executar = False
            self.monitor.desconectar()
            self.area_log.append("Monitoramento parado.")

    def log_callback(self, mensagem):
        """Manipular mensagens de log da thread de monitoramento."""
        if mensagem not in self.mensagens_log:
            self.mensagens_log.add(mensagem)
            self.area_log.append(mensagem)

    def closeEvent(self, event):
        """Manipular o evento de fechamento para ocultar a aplicação em vez de sair."""
        event.ignore()
        self.hide()

    def sair_aplicacao(self):
        """Sair da aplicação e realizar limpeza."""
        if self.monitor:
            self.monitor.executar = False
            self.monitor.desconectar()
        QApplication.quit()

    def salvar_ultimos_inputs(self, broker, topico_pub, topico_sub, usuario, senha):
        """Salvar os últimos inputs usados em um arquivo JSON."""
        dados = {
            "broker": broker,
            "topico_pub": topico_pub,
            "topico_sub": topico_sub,
            "usuario": usuario,
            "senha": senha
        }
        with open('ultimos_inputs.json', 'w') as f:
            json.dump(dados, f)

    def carregar_ultimos_inputs(self):
        """Carregar os últimos inputs usados de um arquivo JSON, se disponível."""
        try:
            with open('ultimos_inputs.json', 'r') as f:
                dados = json.load(f)
                self.broker_input.setText(dados.get("broker", ""))
                self.topico_pub_input.setText(dados.get("topico_pub", ""))
                self.topico_sub_input.setText(dados.get("topico_sub", ""))
                self.usuario_input.setText(dados.get("usuario", ""))
                self.senha_input.setText(dados.get("senha", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Nenhum input anterior encontrado ou erro ao decodificar

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.resize(400, 400)
    ex.show()
    sys.exit(app.exec_())