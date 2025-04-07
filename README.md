# Capsules

<p align="center">
  <img src="./res/icon_background.png" alt="Capsules Logo" width="200"/>
</p>

Capsules is a powerful application for creating and managing secure application containers with full GUI support. Built on Podman's secure rootless container technology, it provides proper desktop integration and a security-first design. Think Docker, but with native desktop integration and without the daemon or root requirements.

## ✨ Key Features

### 🛡️ Security First
- **Rootless Containers**: Powered by Podman for isolation without root privileges
- **Secure GUI**: Isolated X11 applications through Xpra integration

### 🎮 Easy to Use
- **Template System**: Create reusable container templates
- **GUI Management**: Full graphical interface for container management
- **Port Mapping**: Simple host-to-container port forwarding

### 🔧 Flexible Configuration
- **Custom Commands**: Execute commands in containers
- **Persistent Storage**: Overlay filesystem for container persistence

## 🚀 Getting Started

### Prerequisites

#### Required Software
- podman (container runtime)
- xpra (≥ v6.0) for secure GUI forwarding
- python3 and Qt6
- python-pyqt6

### System Configuration

#### Setting up xpra
1. Verify your xpra version:
   ```bash
   xpra --version
   ```
2. Must be version 6.0 or higher
3. Need an update? Visit the [xpra download page](https://github.com/Xpra-org/xpra/wiki/Download)

#### Configuring podman
1. Ensure rootless mode is enabled:
   ```bash
   podman info --format '{{.Host.Security.Rootless}}'
   ```
2. Should return `true`

## 🚀 Installation & Running

### Clone the Repository
```bash
git clone https://github.com/yourusername/capsules.git
cd capsules
```

### Install Dependencies
On Debian/Ubuntu:
```bash
sudo apt install podman xpra python3-pyqt6
```

On Fedora:
```bash
sudo dnf install podman xpra python3-qt6
```

On Arch Linux:
```bash
sudo pacman -S podman xpra python-pyqt6
```

### Run the Application
Make the script executable:
```bash
chmod +x capsules.py
```

Launch Capsules:
```bash
./capsules.py
```

Or run with Python directly:
```bash
python3 capsules.py
```

## 📜 License

This project is licensed under the GNU General Public License v3.0.  
See the [LICENSE](./LICENSE) file for details.