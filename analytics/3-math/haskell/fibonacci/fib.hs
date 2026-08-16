fibonacci :: Int -> Integer
fibonacci n = fst $ foldl (\(a, b) _ -> (b, a + b)) (0, 1) [1..n]

main :: IO()
main = do
    input <- getLine
    putStrLn.show.fibonacci.read $ input