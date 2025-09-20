pub fn add(a: i64, b: i64) -> i64 {
  a + b
}

fn main() {
  let x = 1;
  let y = 2;
  let result = add(x, y);
  match result {
    3 => {
      "three"
    },
    _ => {
      "not three"
    },
  }
}