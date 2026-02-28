import numpy as np
from scipy.fft import fft, ifft
from scipy.linalg import toeplitz

def stran(h):
    h = np.asarray(h).flatten()
    N = len(h)
    nhaf = N // 2
    
    # Создаем вектор частот f точно такой же длины N, как и сигнал h
    # Это критически важно для размера матрицы G
    if N % 2 == 0:
        f = np.concatenate([np.arange(nhaf), np.arange(-nhaf, 0)]) / N
    else:
        f = np.concatenate([np.arange(nhaf + 1), np.arange(-nhaf, 0)]) / N
        
    Hft = fft(h)
    
    # Вычисляем индексы для частот (без нулевой)
    # Нам нужно nhaf штук для формирования HW
    invfk = 1.0 / (1.5 * f[1:nhaf+1])
    
    # W и G должны иметь ширину N (1001 в вашем случае)
    W = 2 * np.pi * np.outer(invfk, f)
    G = np.exp(-(W**2) / 2)
    
    # Формируем Toeplitz. 
    # В Python c - это первый столбец, r - первая строка.
    c = Hft[:nhaf+1]
    r = np.zeros(N, dtype=complex)
    r[0] = Hft[0]
    r[1:] = Hft[:0:-1] # Циклический сдвиг для соответствия MATLAB
    
    HW = toeplitz(c, Hft)
    HW = HW[1:, :] # Убираем строку с нулевой частотой. Теперь размер (nhaf, N)
    
    # Теперь HW (nhaf, N) и G (nhaf, N) — размеры совпадут!
    ST = ifft(HW * G, axis=1)
    
    # Добавляем строку для нулевой частоты
    st0 = np.mean(h) * np.ones((1, N))
    ST = np.vstack([st0, ST])
    
    return ST

def sfk_transform(data, dt, dr, f_min=10, f_max=80, multi_nt=2, multi_nr=10, max_v=400):
    data = np.asarray(data)
    nr, nt = data.shape
    
    # Чтобы избежать ошибок с нечетными числами при multi_nt, 
    # сделаем длину четной
    new_nt = nt * multi_nt
    if new_nt % 2 != 0: new_nt += 1
        
    df = 1 / (new_nt * dt)
    freq_full = np.arange(new_nt // 2 + 1) * df
    
    f_mask = (freq_full >= f_min) & (freq_full <= f_max)
    freq = freq_full[f_mask]
    n_freqs = len(freq)
    
    # Находим индексы маски
    indices = np.where(f_mask)[0]
    if len(indices) == 0:
        return None, None, freq, None, None
    
    min_nf, max_nf = indices[0], indices[-1]

    FTX = np.zeros((n_freqs, nt, nr), dtype=complex)
    
    print(f"Запуск S-преобразования для {nr} трасс...")
    for n in range(nr):
        trace_padded = np.zeros(new_nt)
        trace_padded[:nt] = data[n, :]
        
        st_result = stran(trace_padded)
        # st_result размер (new_nt//2 + 1, new_nt)
        # Берем только нужные частоты и исходное время nt
        FTX[:, :, n] = st_result[min_nf:max_nf+1, :nt]

    # --- Оценка FK и VF ---
    new_nr = nr * multi_nr
    k_axis = np.arange(new_nr) * (1 / (dr * new_nr))
    v_axis = np.linspace(50, max_v, new_nr)
    
    fk2d = np.zeros((n_freqs, new_nr))
    vf2d = np.zeros((new_nr, n_freqs))

    for idx, f in enumerate(freq):
        TX = FTX[idx, :, :] 
        
        line_phase = np.zeros((nr, nt), dtype=complex)
        for jj in range(nt):
            for ii in range(nr):
                idx_t = min(int(np.ceil((jj+1)/nr*(ii+1))) - 1, nt-1)
                line_phase[ii, jj] = TX[idx_t, ii]
        
        fk_t = np.abs(fft(line_phase, n=new_nr, axis=0))
        fk_slice = np.mean(fk_t, axis=1)
        fk2d[idx, :] = fk_slice
        
        if f > 0:
            # Используем векторизацию для ускорения интерполяции скоростей
            k_vals_needed = f / v_axis
            vf2d[:, idx] = np.interp(k_vals_needed, k_axis, fk_slice)

    return fk2d, vf2d, freq, k_axis, v_axis
