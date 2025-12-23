#!/bin/bash

# Script de instalación de PostgreSQL + pgAdmin4
# Compatible con: Debian/Ubuntu (y derivados) y Arch Linux (y derivados como Manjaro/Endeavour)

# Colores
VERDE='\033[0;32m'
AZUL='\033[0;34m'
ROJO='\033[0;31m'
NC='\033[0m'

# Función para detectar la distribución
detectar_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    else
        echo "desconocido"
    fi
}

DISTRO=$(detectar_distro)

echo -e "${AZUL}=== Iniciando instalación para: $DISTRO ===${NC}"

# ==========================================
# BLOQUE PARA DEBIAN / UBUNTU / MINT
# ==========================================
if [[ "$DISTRO" == "debian" || "$DISTRO" == "ubuntu" || "$DISTRO" == "linuxmint" || "$DISTRO" == "pop" ]]; then
    
    echo -e "${VERDE}[DEBIAN] Actualizando e instalando prerequisitos...${NC}"
    sudo apt update && sudo apt install -y curl gnupg2 lsb-release ca-certificates

    echo -e "${VERDE}[DEBIAN] Instalando PostgreSQL...${NC}"
    sudo apt install -y postgresql postgresql-contrib

    echo -e "${VERDE}[DEBIAN] Configurando repositorio pgAdmin4...${NC}"
    curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg
    
    # Detectar codename correctamente (incluso en derivados)
    CODENAME=$(lsb_release -cs)
    # Si es Linux Mint, mapear al codename de Ubuntu correspondiente si es necesario, 
    # pero para simplicidad usaremos el comando directo que suele funcionar o fallar con instrucciones.
    echo "deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$CODENAME pgadmin4 main" | sudo tee /etc/apt/sources.list.d/pgadmin4.list

    echo -e "${VERDE}[DEBIAN] Instalando pgAdmin4 (Web Mode)...${NC}"
    sudo apt update
    sudo apt install -y pgadmin4-web ufw

    echo -e "${AZUL}--- CONFIGURACIÓN POST-INSTALACIÓN (DEBIAN) ---${NC}"
    echo "1. Ejecuta: sudo /usr/pgadmin4/bin/setup-web.sh"
    echo "2. Entra a http://localhost/pgadmin4"

# ==========================================
# BLOQUE PARA ARCH LINUX / MANJARO
# ==========================================
elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" || "$DISTRO" == "endeavouros" ]]; then

    echo -e "${VERDE}[ARCH] Actualizando sistema con pacman...${NC}"
    sudo pacman -Syu --noconfirm

    echo -e "${VERDE}[ARCH] Instalando PostgreSQL y pgAdmin4...${NC}"
    # En Arch, pgadmin4 suele estar en los repos 'extra' como aplicación de escritorio/servidor
    sudo pacman -S --noconfirm postgresql pgadmin4

    echo -e "${VERDE}[ARCH] Inicializando el cluster de base de datos (Paso crítico en Arch)...${NC}"
    # Verificamos si ya existe data para no sobrescribir
    if [ ! -d "/var/lib/postgres/data/base" ]; then
        sudo -u postgres initdb -D /var/lib/postgres/data
        echo -e "${VERDE}Cluster inicializado correctamente.${NC}"
    else
        echo -e "${AZUL}El directorio de datos ya existe, saltando inicialización.${NC}"
    fi

    echo -e "${VERDE}[ARCH] Iniciando y habilitando servicio PostgreSQL...${NC}"
    sudo systemctl enable --now postgresql

    echo -e "${AZUL}--- CONFIGURACIÓN POST-INSTALACIÓN (ARCH) ---${NC}"
    echo "En Arch, pgAdmin4 se instala como aplicación de escritorio nativa."
    echo "Puedes buscar 'pgAdmin 4' en tu menú de aplicaciones o ejecutar 'pgadmin4' en la terminal."

else
    echo -e "${ROJO}Distribución no soportada automáticamente por este script ($DISTRO).${NC}"
    exit 1
fi

# ==========================================
# PASOS COMUNES FINALES
# ==========================================
echo ""
echo -e "${AZUL}=== PROCESO TERMINADO ===${NC}"
echo -e "${VERDE}IMPORTANTE: Configura la contraseña del usuario 'postgres' ahora:${NC}"
echo ""
echo "Ejecuta el siguiente comando manual:"
echo "   sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'tu_nueva_contraseña';\""
echo ""
