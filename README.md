---

# Aplikasi Road Guard - Deteksi Kerusakan Jalan

Aplikasi ini dirancang untuk meningkatkan keselamatan jalan dan pemeliharaan infrastruktur dengan cepat mengidentifikasi dan mengklasifikasikan berbagai jenis kerusakan jalan, seperti lubang jalan dan retakan.


Aplikasi ini didukung oleh model deep learning YOLOv8 yang dilatih dengan dataset Crowdsensing-based Road Damage Detection Challenge 2022.

Model ini dapat mendeteksi empat jenis kerusakan, yaitu:
- Retakan Longitudinal
- Retakan Transversal
- Retakan Aligator
- Lubang Jalan

## Menjalankan di Server Lokal

Berikut adalah langkah-langkah untuk menginstal dan menjalankan aplikasi web di server lokal:

```bash
# Install CUDA jika tersedia
# https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html

# Membuat lingkungan Python
conda create -n road_guard python=3.8
conda activate road_guard

# Install pytorch-CUDA
# https://pytorch.org/get-started/locally/
conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.8 -c pytorch -c nvidia

# Install framework deep learning ultralytics
# https://docs.ultralytics.com/quickstart/
pip install ultralytics

# Install dependencies
pip install -r requirements.txt

# Jalankan webserver streamlit
streamlit run Home.py
```

