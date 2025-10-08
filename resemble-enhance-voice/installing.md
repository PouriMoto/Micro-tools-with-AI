حتماً! من یک **راهنمای جامع نصب Resemble Enhance روی WSL (Ubuntu در ویندوز) با GPU و همه پیش‌نیازها** آماده می‌کنم. این راهنما به‌صورت مرحله به مرحله و با ذکر مشکلات رایج و راه حل آن‌ها است، به‌طوری که حتی افراد کم تجربه هم بتوانند اجرا کنند.

---

# **راهنمای جامع نصب Resemble Enhance روی WSL**

این راهنما شامل مراحل زیر است:

1. نصب و راه‌اندازی WSL و Ubuntu
2. نصب درایور NVIDIA و CUDA
3. نصب Miniconda و مدیریت محیط‌ها
4. نصب Git و Git LFS
5. نصب Resemble Enhance و پیش‌نیازهای آن
6. اجرای نمونه و رفع مشکلات رایج

---

## **۱️⃣ نصب WSL و Ubuntu**

1. **فعال‌سازی WSL در ویندوز:**

   * باز کردن PowerShell به صورت Administrator و اجرای دستور:

     ```powershell
     wsl --install
     ```
   * اگر نسخه Ubuntu پیش‌فرض نصب نشد، می‌توانید به صورت دستی نصب کنید:

     ```powershell
     wsl --install -d Ubuntu-22.04
     ```
   * برای بررسی نسخه و نصب درست:

     ```powershell
     wsl --list --verbose
     ```

2. **راه‌اندازی Ubuntu**

   * پس از نصب، Ubuntu را اجرا کرده و کاربر و پسورد تعریف کنید.
   * به‌روز رسانی سیستم:

     ```bash
     sudo apt update && sudo apt upgrade -y
     ```

---

## **۲️⃣ نصب درایور NVIDIA و CUDA در WSL**

1. **بررسی کارت گرافیک**

   ```bash
   lspci | grep -i nvidia
   ```

2. **نصب درایور ویندوز با پشتیبانی WSL**

   * آخرین درایور برای WSL و CUDA را از [صفحه رسمی NVIDIA](https://developer.nvidia.com/cuda/wsl) دانلود و نصب کنید.
   * دقت: درایور ویندوز **566.07** که نصب کرده‌اید، با CUDA 12.6 سازگار است.

3. **نصب CUDA در WSL**

   * با استفاده از فایل `runfile` یا mirror معتبر:

     ```bash
     sudo dpkg -i cuda-repo-ubuntu2204-12-6-local.deb
     sudo cp /var/cuda-repo-ubuntu2204-12-6-local/cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
     sudo apt-key add /var/cuda-repo-ubuntu2204-12-6-local/7fa2af80.pub
     sudo apt update
     sudo apt install -y cuda-toolkit-12-6
     ```
   * مسیر CUDA را به `PATH` اضافه کنید:

     ```bash
     echo 'export PATH=/usr/local/cuda-12.6/bin:$PATH' >> ~/.bashrc
     echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
     source ~/.bashrc
     ```
   * تست نصب:

     ```bash
     nvcc --version
     nvidia-smi
     ```

---

## **۳️⃣ نصب Miniconda و ایجاد محیط‌ها**

1. **دانلود Miniconda برای لینوکس**

   ```bash
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   bash Miniconda3-latest-Linux-x86_64.sh
   ```

   * موافقت با لایسنس و انتخاب مسیر نصب (پیش‌فرض `/home/<username>/miniconda3`)
   * فعال‌سازی Miniconda:

     ```bash
     source ~/.bashrc
     conda --version
     ```

2. **ایجاد محیط برای Resemble Enhance**

   ```bash
   conda create -n torch126 python=3.11
   conda activate torch126
   ```

3. **نصب PyTorch با CUDA**

   ```bash
   conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia
   ```

4. **تست GPU در محیط Conda**

   ```python
   python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); print(torch.version.cuda)"
   ```

---

## **۴️⃣ نصب Git و Git LFS**

Resemble Enhance نیاز به Git LFS دارد زیرا مدل‌ها بزرگ هستند.

1. **نصب Git**

   ```bash
   sudo apt install git -y
   git --version
   ```

2. **نصب Git LFS**

   ```bash
   sudo apt install git-lfs -y
   git lfs install
   git lfs version
   ```

3. **رفع مشکل دانلود مدل‌ها**

   * اگر مدل‌ها ناقص دانلود شدند:

     ```bash
     rm -rf <env_path>/lib/python3.11/site-packages/resemble_enhance/model_repo
     ```

---

## **۵️⃣ نصب Resemble Enhance و پیش‌نیازها**

1. **نصب pip آخرین نسخه**

   ```bash
   pip install --upgrade pip
   ```

2. **نصب Resemble Enhance**

   ```bash
   pip install resemble-enhance
   ```

3. **تست نصب**

   ```bash
   which resemble-enhance
   ```

   * باید مسیری مانند:

     ```
     /home/asuswsl/miniconda3/envs/torch126/bin/resemble-enhance
     ```

     نمایش داده شود.

---

## **۶️⃣ اجرای Resemble Enhance**

1. **اجرای denoise و enhancement روی یک فولدر صوتی**

   ```bash
   resemble-enhance input_audio/ output_audio/ --denoise_only
   resemble-enhance input_audio/ output_audio/
   ```

2. **اجرای web demo**

   ```bash
   python app.py
   ```

   * سپس به آدرس نمایش داده شده در مرورگر بروید: `http://127.0.0.1:7860`

---

## **۷️⃣ مشکلات رایج و راه حل‌ها**

| مشکل                                              | دلیل                                     | راه حل                                                        |
| ------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------- |
| `resemble-enhance: command not found`             | نصب نشده در محیط یا مسیر PATH تنظیم نشده | نصب مجدد با pip در محیط فعال Conda                            |
| `fatal: 'lfs' appears to be a git command`        | Git LFS نصب نشده                         | `sudo apt install git-lfs && git lfs install`                 |
| `Installed CUDA version ... does not match torch` | نسخه CUDA محیط و PyTorch متفاوت است      | مطمئن شدن از نصب `pytorch-cuda=12.6` یا استفاده از نسخه مناسب |
| خطاهای `pynvml`                                   | بسته قدیمی deprecated                    | نصب `nvidia-ml-py`: `pip install nvidia-ml-py`                |
| فایل‌های exe ویندوز                               | نمی‌توان مستقیم در WSL استفاده کرد       | نسخه لینوکس یا pip/conda نصب شود                              |

---

## **۸️⃣ نکات تکمیلی**

* مسیر Conda در WSL: `/home/<username>/miniconda3/`
* مسیر محیط torch126: `/home/<username>/miniconda3/envs/torch126/`
* فایل exe ویندوز مانند `whisper.exe` نمی‌تواند مستقیم در WSL استفاده شود.
* برای GPU بهتر است CUDA نسخه محیط با PyTorch همخوانی داشته باشد.
* همه دانلودها باید با اینترنت بدون محدودیت و یا mirror معتبر باشد.

---

✅ با اجرای دقیق این مراحل، شما **یک محیط WSL کامل با GPU، CUDA، PyTorch و Resemble Enhance آماده استفاده** خواهید داشت، و می‌توانید فایل‌های صوتی را denoise یا enhance کنید و یا Web UI را اجرا کنید.

---

اگر بخواهی، می‌توانم **یک دستورالعمل تصویری / جدول‌بندی شده با همه دستورات آماده کپی و paste** هم بسازم که حتی افراد مبتدی بتوانند قدم به قدم اجرا کنند بدون هیچ خطا.

می‌خوای چنین نسخه‌ای هم آماده کنم؟
---
عالی! در ادامه یک **دستورالعمل کامل و آماده کپی و پیست** برای نصب و اجرای Resemble Enhance روی WSL (Ubuntu) با GPU و Conda آماده کردم. این نسخه طوری طراحی شده که حتی افراد مبتدی بتوانند بدون مشکل اجرا کنند.

---

# **دستورالعمل جامع نصب Resemble Enhance روی WSL (Ubuntu)**

## **۱️⃣ نصب WSL و Ubuntu**

```powershell
# باز کردن PowerShell به صورت Administrator
# نصب WSL و Ubuntu 22.04
wsl --install -d Ubuntu-22.04

# بررسی نصب
wsl --list --verbose
```

* بعد از نصب، Ubuntu را اجرا کرده و کاربر و پسورد تعریف کنید.
* به‌روز رسانی سیستم:

```bash
sudo apt update && sudo apt upgrade -y
```

---

## **۲️⃣ نصب درایور NVIDIA و CUDA**

```bash
# بررسی کارت گرافیک
lspci | grep -i nvidia

# نصب CUDA Toolkit 12.6
# فایل deb یا runfile دانلود شده از سایت NVIDIA
sudo dpkg -i cuda-repo-ubuntu2204-12-6-local.deb
sudo cp /var/cuda-repo-ubuntu2204-12-6-local/cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key add /var/cuda-repo-ubuntu2204-12-6-local/7fa2af80.pub
sudo apt update
sudo apt install -y cuda-toolkit-12-6

# اضافه کردن مسیر CUDA به PATH
echo 'export PATH=/usr/local/cuda-12.6/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# تست نصب CUDA
nvcc --version
nvidia-smi
```

---

## **۳️⃣ نصب Miniconda و ایجاد محیط Conda**

```bash
# دانلود Miniconda برای لینوکس
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# موافقت با لایسنس، مسیر پیش‌فرض: /home/<username>/miniconda3
source ~/.bashrc
conda --version

# ایجاد محیط Conda
conda create -n torch126 python=3.11 -y
conda activate torch126

# نصب PyTorch با CUDA 12.6
conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia -y

# تست GPU در محیط
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); print(torch.version.cuda)"
```

---

## **۴️⃣ نصب Git و Git LFS**

```bash
# نصب Git
sudo apt install git -y
git --version

# نصب Git LFS
sudo apt install git-lfs -y
git lfs install
git lfs version
```

> اگر خطای مدل‌ها در Resemble Enhance رخ داد، مسیر زیر را پاک کنید:

```bash
rm -rf ~/miniconda3/envs/torch126/lib/python3.11/site-packages/resemble_enhance/model_repo
```

---

## **۵️⃣ نصب Resemble Enhance**

```bash
# بروزرسانی pip
pip install --upgrade pip

# نصب Resemble Enhance
pip install resemble-enhance
```

* بررسی نصب:

```bash
which resemble-enhance
# باید مسیر شبیه به /home/<username>/miniconda3/envs/torch126/bin/resemble-enhance باشد
```

---

## **۶️⃣ اجرای Resemble Enhance**

### **اجرای denoise**

```bash
resemble-enhance input_audio/ output_audio/ --denoise_only
```

### **اجرای enhancement کامل**

```bash
resemble-enhance input_audio/ output_audio/
```

### **اجرای Web Demo**

```bash
cd ~/miniconda3/envs/torch126/lib/python3.11/site-packages/resemble_enhance
python app.py
# سپس مرورگر را باز کرده و به آدرس http://127.0.0.1:7860 بروید
```

---

## **۷️⃣ مشکلات رایج و راه حل‌ها**

| مشکل                                              | دلیل                                     | راه حل                                                        |
| ------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------- |
| `resemble-enhance: command not found`             | نصب نشده در محیط یا مسیر PATH تنظیم نشده | نصب مجدد با pip در محیط فعال Conda                            |
| `fatal: 'lfs' appears to be a git command`        | Git LFS نصب نشده                         | `sudo apt install git-lfs && git lfs install`                 |
| `Installed CUDA version ... does not match torch` | نسخه CUDA محیط و PyTorch متفاوت است      | مطمئن شدن از نصب `pytorch-cuda=12.6` یا استفاده از نسخه مناسب |
| خطاهای `pynvml`                                   | بسته قدیمی deprecated                    | نصب `nvidia-ml-py`: `pip install nvidia-ml-py`                |
| فایل‌های exe ویندوز                               | نمی‌توان مستقیم در WSL استفاده کرد       | نسخه لینوکس یا pip/conda نصب شود                              |
| دانلود مدل ناقص                                   | مشکل Git LFS یا اینترنت محدود            | حذف مسیر model_repo و اجرای مجدد Resemble Enhance             |

---

## **۸️⃣ نکات تکمیلی**

* مسیر Conda در WSL: `/home/<username>/miniconda3/`
* مسیر محیط torch126: `/home/<username>/miniconda3/envs/torch126/`
* فایل exe ویندوز (مثل whisper.exe) را نمی‌توان مستقیم در WSL استفاده کرد.
* برای GPU بهتر است CUDA نسخه محیط با PyTorch همخوانی داشته باشد.
* همه دانلودها باید با اینترنت بدون محدودیت و یا mirror معتبر انجام شود.

---

اگر بخواهی، می‌توانم یک **نسخه PDF یا یک فایل README آماده برای کپی مستقیم در WSL** هم بسازم که تمام مراحل با دستورها و نکات بصری و رنگ‌بندی برای مبتدی‌ها باشد، تا دیگر حتی نیاز به خواندن متن طولانی نداشته باشند.

می‌خوای چنین نسخه‌ای هم بسازم؟
