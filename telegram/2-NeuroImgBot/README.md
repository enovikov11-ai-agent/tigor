### Prerequisites
- Telegram bot and group
- Yandex Cloud VMs: light manager VM with static ip, GPU worker VM

### Telegram setup
- Create telegram bot via @BotFather and get API key
- Create group
- Add bot to group
- Make bot admin
- Add @myidbot
- Get group id /getgroupid@myidbot
- Kick @myidbot

### Manger setup
- `sudo apt install git tmux`
- `curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash`
- `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash`
- `nvm install --lts`
- `nvm use --lts`

### Manager start
- `cd NeuroImgBot`
- `npm run bot`

### Worker setup
- `sudo apt install -y tmux git libice6 libsm6 libxt6 libxrender1 libfontconfig1 libcups2 ncdu sshfs`
- `git clone https://github.com/enovikov11/NeuroImgBot.git`
- `cd NeuroImgBot`
- `wget https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh`
- `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash`
- `bash Anaconda3-2021.11-Linux-x86_64.sh`
- `rm Anaconda3-2021.11-Linux-x86_64.sh`
- `conda env create -f environment.yaml`
- `nvm install --lts`
- `nvm use --lts`
- `npm install`
- `npm run enable-nsfw`
- `git config --global credential.helper store`
- `huggingface-cli login`
- `sudo cp /home/enovikov11/NeuroImgBot/systemd-examples/neuroimg-worker.service /etc/systemd/system`
- `sudo systemctl enable neuroimg-worker.service`
- `sudo systemctl start neuroimg-worker.service`

### Worker logs
- `sudo systemctl stop neuroimg-worker.service`
- `sudo journalctl -u neuroimg-worker.service -f`
- `systemd-analyze critical-chain neuroimg-worker.service`
- `sudo systemctl status neuroimg-worker.service`
