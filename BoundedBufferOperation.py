import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class BoundedBuffer(QObject):
    buffer_updated = pyqtSignal(list)
    action_updated = pyqtSignal(str)

    def __init__(self, capacity=20):
        super().__init__()
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.empty = threading.Semaphore(capacity)
        self.full = threading.Semaphore(0)
        self.lock = threading.Lock()
        self.counter = 1  # 初始化计数器为1

    def produce(self, producer_id):
        item = None
        with self.lock:
            if self.counter <= self.capacity:
                item = self.counter
                self.counter += 1
        if item is not None:
            self.empty.acquire()
            with self.lock:
                for i in range(self.capacity):
                    if self.buffer[i] is None:
                        self.buffer[i] = item
                        break
            self.full.release()
            self.buffer_updated.emit(self.buffer)
            action_text = f'生产者 {producer_id} 生产了 {item}'
            self.action_updated.emit(action_text)  # 发送生产者生产的信号

    def consume(self, consumer_id):
        self.full.acquire()
        item = None
        with self.lock:
            for i in range(self.capacity):
                if self.buffer[i] is not None:
                    item = self.buffer[i]
                    self.buffer[i] = None
                    break
        self.empty.release()
        self.buffer_updated.emit(self.buffer)
        action_text = f'消费者 {consumer_id} 消费了 {item}'
        self.action_updated.emit(action_text)  # 发送消费者消费的信号
        return item


class ProducerConsumerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('生产者消费者应用')
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.buffer_label = QLabel()
        self.buffer_label.setWordWrap(True)
        self.buffer_label.setMinimumWidth(600)  # 设置最小宽度
        layout.addWidget(self.buffer_label)

        self.action_text_edit = QTextEdit()  # 用于显示生产和消费的动作
        self.action_text_edit.setReadOnly(True)
        layout.addWidget(self.action_text_edit)

        # 添加输入框和按钮
        self.producer_count_edit = QLineEdit()
        self.consumer_count_edit = QLineEdit()
        self.start_button = QPushButton("开始")

        layout.addWidget(QLabel("生产者数量:"))
        layout.addWidget(self.producer_count_edit)
        layout.addWidget(QLabel("消费者数量:"))
        layout.addWidget(self.consumer_count_edit)
        layout.addWidget(self.start_button)

        self.start_button.clicked.connect(self.start_threads)

        self.buffer = None

    def start_threads(self):
        # 获取用户输入的生产者和消费者数量
        producer_count = int(self.producer_count_edit.text())
        consumer_count = int(self.consumer_count_edit.text())

        # 创建有界缓冲区
        self.buffer = BoundedBuffer()

        # 创建生产者线程，并记录它们初始生产的物品
        initial_produced_items = []
        for i in range(producer_count):
            initial_item = i + 1
            initial_produced_items.append(initial_item)
            producer = threading.Thread(target=self.producer_task, args=(i + 1, initial_item))
            producer.start()

        # 创建消费者线程
        for i in range(consumer_count):
            consumer = threading.Thread(target=self.consumer_task, args=(i + 1,))
            consumer.start()

        # 手动触发一次界面更新
        self.update_buffer_label(self.buffer.buffer)

        # 手动发射初始生产动作的信号
        for item in initial_produced_items:
            action_text = f'生产者 初始生产了 {item}'
            self.update_action_text(action_text)

        # 监听有界缓冲区更新
        self.buffer.buffer_updated.connect(self.update_buffer_label)
        # 监听生产和消费的动作
        self.buffer.action_updated.connect(self.update_action_text)

    def producer_task(self, id, initial_item):
        while True:
            self.buffer.produce(id)
            time.sleep(1)  # 模拟一些工作

    def consumer_task(self, id):
        while True:
            time.sleep(2)  # 模拟一些工作
            item = self.buffer.consume(id)

    @pyqtSlot(list)
    def update_buffer_label(self, buffer):
        buffer_str = ', '.join(str(item) if item is not None else '-' for item in buffer)
        current_position = sum(1 for item in buffer if item is not None)
        self.buffer_label.setText(
            f'缓冲区内容:\n[{buffer_str}]\n当前位置: {current_position}')

    @pyqtSlot(str)
    def update_action_text(self, action):
        current_text = self.action_text_edit.toPlainText()
        new_text = f'{current_text}\n{action}'
        self.action_text_edit.setPlainText(new_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProducerConsumerApp()
    window.show()
    sys.exit(app.exec_())
