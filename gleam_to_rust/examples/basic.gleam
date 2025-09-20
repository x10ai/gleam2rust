pub fn add(a: Int, b: Int) -> Int {
  a + b
}

fn main() {
  let x = 1
  let y = 2
  let result = add(x, y)
  case result {
    3 -> "three"
    _ -> "not three"
  }
}
