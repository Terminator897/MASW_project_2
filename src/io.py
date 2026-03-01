from obspy import read
import numpy as np

def load_seismic_file(file_path):
    """
    Универсальное чтение SEGY/SGY/SU с автоматическим определением параметров.
    """
    # format=None заставляет ObsPy угадывать формат (SEGY, SU и т.д.)
    stream = read(file_path)
    
    # Конвертируем в матрицу (трассы x отсчеты времени)
    data = np.array([tr.data for tr in stream])
    
    # dt берем из первого заголовка
    dt = stream[0].stats.delta
    
    # Пытаемся вытянуть геометрию
    dr_auto = 2.0  # Значение по умолчанию
    x0_auto = 0.0
    
    try:
        # 1. Пробуем найти расстояние в метаданных ObsPy
        # Если в SEGY заполнено поле 'distance' (байты 37-40 в заголовке трассы)
        offsets = [tr.stats.distance for tr in stream if 'distance' in tr.stats]
        
        if len(offsets) >= 2:
            x0_auto = float(offsets[0])
            dr_auto = float(abs(offsets[1] - offsets[0]))
        else:
            # 2. Если 'distance' нет, пробуем координаты X (байты 73-76)
            coords = [tr.stats.segy.trace_header.group_coordinate_x for tr in stream]
            # В SEGY координаты часто хранятся с множителем (байты 71-72)
            scalar = stream[0].stats.segy.trace_header.scalar_to_be_applied_to_all_coordinates
            if scalar < 0:
                coords = [c / abs(scalar) for c in coords]
            elif scalar > 0:
                coords = [c * scalar for c in coords]
                
            if len(coords) >= 2:
                x0_auto = float(coords[0])
                dr_auto = float(abs(coords[1] - coords[0]))
    except Exception as e:
        print(f"Предупреждение: не удалось считать dr/x0 из заголовков: {e}")
        
    return stream, data, dt, dr_auto, x0_auto