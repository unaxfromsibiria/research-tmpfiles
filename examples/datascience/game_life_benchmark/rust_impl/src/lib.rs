use std;

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
