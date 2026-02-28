import numpy as np
from scipy.fft import fft, ifft
from scipy.linalg import toeplitz

def stran(h, s_width=1.5): # Добавили s_width
    h = np.asarray(h).flatten()
    N = len(h)
    nhaf = N // 2
    
    if N % 2 == 0:
        f = np.concatenate([np.arange(nhaf), np.arange(-nhaf, 0)]) / N
    else:
        f = np.concatenate([np.arange(nhaf + 1), np.arange(-nhaf, 0)]) / N
        
    Hft = fft(h)
    # Используем s_width из параметров
    invfk = 1.0 / (s_width * f[1:nhaf+1])
    
    W = 2 * np.pi * np.outer(invfk, f)
    G = np.exp(-(W**2) / 2)
    
    c = Hft[:nhaf+1]
    r = np.zeros(N, dtype=complex)
    r[0] = Hft[0]
    r[1:] = Hft[:0:-1]
    
    HW = toeplitz(c, Hft)
    HW = HW[1:, :]
    ST = ifft(HW * G, axis=1)
    
    st0 = np.mean(h) * np.ones((1, N))
    ST = np.vstack([st0, ST])
    return ST

def sfk_transform(data, dt, dr, f_min=5, f_max=80, v_min=50, v_max=500, 
                  multi_nt=2, multi_nr=20, s_width=1.5):
    # Теперь все параметры передаются снаружи
    data = np.asarray(data)
    nr, nt = data.shape
    new_nt = nt * multi_nt
    if new_nt % 2 != 0: new_nt += 1
        
    df = 1 / (new_nt * dt)
    freq_full = np.arange(new_nt // 2 + 1) * df
    f_mask = (freq_full >= f_min) & (freq_full <= f_max)
    freq = freq_full[f_mask]
    n_freqs = len(freq)
    
    indices = np.where(f_mask)[0]
    min_nf, max_nf = indices[0], indices[-1]

    FTX = np.zeros((n_freqs, nt, nr), dtype=complex)
    
    for n in range(nr):
        trace_padded = np.zeros(new_nt)
        trace_padded[:nt] = data[n, :]
        st_result = stran(trace_padded, s_width=s_width) # Передаем s_width
        FTX[:, :, n] = st_result[min_nf:max_nf+1, :nt]

    new_nr = nr * multi_nr
    k_axis = np.arange(new_nr) * (1 / (dr * new_nr))
    v_axis = np.linspace(v_min, v_max, new_nr) # Используем v_min
    
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
            k_vals_needed = f / v_axis
            vf2d[:, idx] = np.interp(k_vals_needed, k_axis, fk_slice)

    return fk2d, vf2d, freq, k_axis, v_axis