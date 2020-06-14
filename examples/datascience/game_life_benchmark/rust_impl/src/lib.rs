use std::thread;
use std;
use std::sync::{Arc, Mutex};

const NEIGHBORS_COUNT: usize = 8;
const X_DELTA: [i32; NEIGHBORS_COUNT] = [-1, 0, 1, -1, 1, -1, 0, 1];
const Y_DELTA: [i32; NEIGHBORS_COUNT] = [-1, -1, -1, 0, 0, 1, 1, 1];


#[no_mangle]
pub extern "C" fn make_step(src: *const i32, size: i32) -> *mut i32 {
    let full_size: usize = (size + 2) as usize;
    let len = (full_size * full_size) as usize;
    let n = (size + 1) as usize;
    let mut k: usize;
    let mut m;
    let mut arr: Vec<i32> = Vec::new();
    arr.resize(len, 0i32);

    unsafe {
        let src_arr = std::slice::from_raw_parts(src, len);
        for i in 1..n {
            for j in 1..n {
                k = i + j * full_size;
                m = 0;
                for l in 0..NEIGHBORS_COUNT {
                    if src_arr[(i as i32 + X_DELTA[l]) as usize + (j as i32 + Y_DELTA[l]) as usize * full_size] > 0 {
                        m += 1;
                    }
                }
                if (m == 3) || (src_arr[k] > 0 && m == 2) {
                    arr[k] = 1;
                }
            }
        }
    }
    let p = arr.as_mut_ptr();
    std::mem::forget(arr);
    p
}

#[no_mangle]
pub extern "C" fn make_step_update(src: *mut i32, size: i32) -> i32 {
    let full_size: usize = (size + 2) as usize;
    let len = (full_size * full_size) as usize;
    let n = (size + 1) as usize;
    let mut k: usize;
    let mut m;

    unsafe {
        let arr = std::slice::from_raw_parts_mut(src, len);
        let src_arr: Vec<i32> = arr.to_vec();

        for i in 1..n {
            for j in 1..n {
                k = i + j * full_size;
                m = 0;
                for l in 0..NEIGHBORS_COUNT {
                    if src_arr[(i as i32 + X_DELTA[l]) as usize + (j as i32 + Y_DELTA[l]) as usize * full_size] > 0 {
                        m += 1;
                    }
                }
                arr[k] = if (m == 3) || (src_arr[k] > 0 && m == 2) {
                    1
                } else {
                    0
                }
            }
        }
    }
    len as i32
}

#[no_mangle]
pub extern "C" fn make_step_mt(src: *const i32, size: i32, cpu_count: i32) -> *mut i32 {
    let full_size: usize = (size + 2) as usize;
    let len = (full_size * full_size) as usize;
    let n = (size + 1) as usize;
    let part = (size / cpu_count) as usize;
    let mut arr: Vec<i32> = Vec::new();
    arr.resize(len, 0i32);
    let mut arr_result = arr.clone();
    let p_count = cpu_count as usize;
    let arr_arc = Arc::new(Mutex::new(arr));

    unsafe {
        let src_arr = std::slice::from_raw_parts(src, len);
        for p_index in 0..p_count {
            let ps_arr = arr_arc.clone();

            thread::spawn(move || {
                let mut k: usize;
                let mut m;
                let a = part * p_index;
                let mut b = a + part;
                if p_index + 1 == p_count {
                    b = size as usize;
                }
                for p_i in a..b {
                    let i = p_i + 1;
                    for j in 1..n {
                        k = i + j * full_size;
                        m = 0;
                        for l in 0..NEIGHBORS_COUNT {
                            if src_arr[(i as i32 + X_DELTA[l]) as usize + (j as i32 + Y_DELTA[l]) as usize * full_size] > 0 {
                                m += 1;
                            }
                        }
                        if (m == 3) || (src_arr[k] > 0 && m == 2) {
                            let mut arr_ptr = ps_arr.lock().unwrap();
                            (*arr_ptr)[k] = 1;
                        }
                    }
                }
            }).join().unwrap();
        }
    }

    let arr_ptr = arr_arc.lock().unwrap();
    let mut k: usize;
    for i in 1..n {
        for j in 1..n {
            k = i + j * full_size;
            arr_result[k] = (*arr_ptr)[k];
        }
    }
    let p = arr_result.as_mut_ptr();
    std::mem::forget(arr_result);
    p
}
