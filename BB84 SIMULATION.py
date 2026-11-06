#!/usr/bin/env python
# coding: utf-8

# In[1]:





# In[13]:


from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
class Qubit(metaclass =ABCMeta):
    @abstractmethod
    def h(self): pass
    @abstractmethod
    def x(self): pass
    @abstractmethod
    def measure(self) -> bool: pass
    @abstractmethod
    def reset(reset): pass 
class QuantumDevice (metaclass=ABCMeta):
    @abstractmethod
    def allocate_qubit(self) -> Qubit:
        pass
    @abstractmethod
    def deallocate_qubit(self, qubit :Qubit):
        pass
    @contextmanager
    def using_qubit(self):
        qubit = self.allocate_qubit()
        try:
            yield qubit
        finally:
            qubit.reset()
            self.deallocate_qubit(qubit)


# In[14]:


class SingleQubitSimulator(QuantumDevice):
    def allocate_qubit(self) -> Qubit:
        return SimulatedQubit()
        
    def deallocate_qubit(self, qubit: Qubit):
        pass 


# In[15]:


import numpy as np
KET_0 = np.array ([
    [1],
    [0]
], dtype = complex)
H = np.array ([
    [1, 1],
    [1, -1]
], dtype = complex)/np.sqrt(2)
X = np.array([
    [0, 1],
    [1, 0]
], dtype=complex)
Z = np.array([
    [1, 0],
    [0, -1]
], dtype=complex)
class SimulatedQubit(Qubit):
    def __init__ (self):
        self.reset()
    def h(self):
        self.state = H @ self.state
    def x(self):
        self.state = X @ self.state
    def z(self):
        self.state = Z @ self.state
    def measure(self) ->bool:
        pr0 = np.abs(self.state[0, 0]) ** 2
        sample = np.random.random() <= pr0
        return bool (0 if sample else 1)
    def reset (self):
        self.state = KET_0.copy()


# In[16]:


def bits_to_text(bit_list):
    bit_string = "".join(str(b) for b in bit_list)
    chars = []
    for i in range(0, len(bit_string), 8):
        byte_chunk = bit_string[i : i + 8]
        if len(byte_chunk) == 8:
            char_code = int(byte_chunk, 2)
            chars.append(chr(char_code))
    return "".join(chars)


# In[17]:


def prepare_classical_message_plusminus (bit : bool, q : Qubit) -> None:
    if bit:
        q.x()
    q.h()
def eve_measure_plusminus(q:Qubit) -> bool:
    q.h()
    return q.measure()
def send_classical_bit_plusminus (device: QuantumDevice, bit:bool) -> None:
    with device.using_qubit() as q:
        prepare_classical_message_plusminus(bit,q)
        result = eve_measure_plusminus(q)
        assert result == bit


# In[18]:


def prepare_classical_message(bit:bool, q:Qubit) -> None:
    if bit:
        q.x()
def eve_measure(q:Qubit) -> bool:
    return q.measure()
def send_classical_bit(device:QuantumDevice, bit:bool) -> None:
    with device.using_qubit() as q:
        prepare_classical_message(bit, q)
        result = eve_measure(q)
        q.reset()
    assert result == bit


# In[19]:


from typing import List
def sample_random_bit (device: QuantumDevice) -> bool:
    with device.using_qubit() as q:
        q.h()
        result = q.measure()
        q.reset()
    return result
def prepare_message_qubit (message: bool, basis: bool, q:Qubit) -> None:
    if message:
        q.x()
    if basis:
        q.h()
def measure_message_qubit(basis:bool, q:Qubit) -> bool:
    if basis:
        q.h()
    result = q.measure()
    q.reset()
    return result
def convert_to_hex(bits: List[bool]) ->str:
    return hex(int(
        "".join(["1" if bit else "0" for bit in bits]),
    ))


# In[32]:


def apply_phase_flip_noise(q: Qubit, p: float, noise_type: str = 'Z') -> None:
    if noise_type == 'Z':
        if np.random.rand() < p:
            q.z()
    elif noise_type == 'X':
        if np.random.rand() <p:
            q.x()
    elif noise_type == 'depolarizing':
        r = np.random.rand()
        if r < p/3: 
            q.x()
        elif r < 2*p/3:
            q.z()
            q.x()
        elif r < p:
            q.z()
            
def send_single_bit_with_bb84 (your_device: QuantumDevice, eve_device:QuantumDevice, p:float, noise_type: str = 'Z') ->tuple:
    [your_message, your_basis] = [sample_random_bit(your_device) for _ in range(2)
                                 ]
    eve_basis = sample_random_bit (eve_device)
    with your_device.using_qubit() as q:
        prepare_message_qubit(your_message, your_basis, q)
        apply_phase_flip_noise(q, p, noise_type)
        eve_result = measure_message_qubit(eve_basis, q)
    return ((your_message, your_basis), (eve_result, eve_basis))


# In[33]:


def apply_one_time_pad(message: List[bool], key: List[bool]) ->List[bool]:
    return [
        message_bit ^ key_bit
        for (message_bit, key_bit) in zip(message, key)
    ]


# In[34]:


def simulate_bb84(n_bits :int, p: float, noise_type: str = 'Z') -> tuple:
    your_device = SingleQubitSimulator()
    eve_device = SingleQubitSimulator ()
    alice_key = []
    bob_key = []
    n_rounds = 0
    errors = 0
    while len(alice_key) < n_bits:
        n_rounds += 1
        ((your_message, your_basis), (eve_result, eve_basis)) = \
        send_single_bit_with_bb84(your_device, eve_device, p, noise_type)
        if your_basis == eve_basis:
            alice_key.append (your_message)
            bob_key.append (eve_result)
            if your_message != eve_result:
                errors +=1
            qber = errors / len(alice_key) if len(alice_key) > 0 else 0
    return alice_key, bob_key, n_rounds, qber


# In[35]:


p_list = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
results = []
for p in p_list:
    alice_key, bob_key, rounds, qber = simulate_bb84(n_bits=96, p=p, noise_type = 'Z')
    results.append({
    'p':p,
    'rounds': rounds,
    'qber' : qber
    })


# In[36]:


def text_to_bits(text: str) -> list:
    """Hàm chuyển đổi chữ viết thông thường thành danh sách các bit 0 và 1"""
    bit_list = []
    for char in text:
        binary_string = bin(ord(char))[2:].zfill(8)
        for bit in binary_string:
            bit_list.append(int(bit))
            
    return bit_list

    
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
st.set_page_config(
    page_title = "QUANTUM KEY DISTRIBUTION BB84 SIMULATION",
    page_icon = "⚛️",
    layout = "wide"
)
st.title("⚛️ BB84 Quantum Key Distribution Performance Analysis")
st.caption("Hệ thống phân tích ảnh hưởng của nhiễu lượng tử đến độ an toàn của khóa và khả năng truyền tin.")
st.sidebar.header("Tham số kênh truyền")
p = st.sidebar.slider ("Xác suất nhiễu p:", min_value=0.0, max_value=0.5, value=0.1, step=0.01)
col_alice, col_bob = st.columns([1, 1], gap="large")
with col_alice:
    with st.container(border=True):
        st.subheader("👩‍💻 Trạm truyền tin (Alice)")
        secret_text = st.text_input("Nhập văn bản:")
        
        st.markdown("---")
        start_button = st.button("🚀 Bắt đầu truyền tin Lượng tử", type="primary", use_container_width=True)


with col_bob:
    with st.container(border=True):
        st.subheader("👨‍💻 Trạm nhận tin (Bob)")
        
        if start_button:
            message = text_to_bits(secret_text)
            key_length = len(message)
            tab_z, tab_x, tab_depol = st.tabs(["Phase Flip (Z)", "Bit Flip (X)", "Depolarizing"])
            noise_models = [
                (tab_z, 'Z'),
                (tab_x, 'X'),
                (tab_depol, 'depolarizing')
            ]
            
            for tab, noise_type in noise_models:
                with tab:
                    alice_key, bob_key, rounds, qber = simulate_bb84(key_length, p, noise_type=noise_type)
                    
                    encrypted = apply_one_time_pad(message, alice_key)
                    decrypted = apply_one_time_pad(encrypted, bob_key)
                    final_text = bits_to_text(decrypted)
                    
                    m1, m2 = st.columns(2)
                    m1.metric(label="Tổng số vòng (Rounds)", value=f"{rounds}")
                    m2.metric(
                        label="Tỷ lệ lỗi (QBER)", 
                        value=f"{qber * 100:.2f}%", 
                        delta="> 11% (Nguy hiểm)" if qber > 0.11 else "≤ 11% (An toàn)",
                        delta_color="inverse" if qber > 0.11 else "normal"
                    )
                    
                    st.write("**Văn bản Bob giải mã:**")
                    st.code(final_text, language="text")
                    
                    st.write("**Khóa Lượng tử :**")
                    col_k1, col_k2 = st.columns(2)
                    with col_k1:
                        st.caption("Khóa Alice:")
                        st.code(convert_to_hex(alice_key))
                    with col_k2:
                        st.caption("Khóa Bob:")
                        st.code(convert_to_hex(bob_key))
                    
                    if qber > 0.11:
                        st.error("⚠️ **QBER > 11% (Vượt ngưỡng Shor-Preskill):** Phát hiện nhiễu cao/nghe lén ➔ HUỶ KHÓA!")
                    else:
                        st.success("✅ **QBER ≤ 11%:** Khóa an toàn, thiết lập liên lạc thành công!")
        else:
            st.info("👈 Nhập văn bản ở trạm Alice và nhấn nút **Bắt đầu truyền tin** để xem kết quả.")









