from obspy import read
import numpy as np

def load_seismic_file(file_path):
    """Читает SEGY/SU и возвращает поток, матрицу данных и шаг dt."""
    stream = read(file_path)
    # Трассы в строки, отсчеты в столбцы: (n_traces, n_samples)
    data = np.array([tr.data for tr in stream])
    dt = stream[0].stats.delta
    return stream, data, dt