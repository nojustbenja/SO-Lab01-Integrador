from pathlib import Path
from collections import Counter
from queue import Queue
from threading import Thread, Lock
from datetime import datetime
import shutil

BASE = Path.home() / "laboratorio_so"
ENTRADA = BASE / "data" / "entrada"
PROCESADOS = BASE / "data" / "procesados"
REPORTES = BASE / "data" / "reportes"
LOG = BASE / "logs" / "sistema.log"
