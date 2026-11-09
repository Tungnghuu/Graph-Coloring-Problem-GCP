from benchmark import parse_args, run_benchmark


if __name__ == "__main__":
    args = parse_args()
    run_benchmark(
        args.dataset,
        args.methods,
        args.encodings,
        args.time_limit,
        args.output,
        args.limit,
    )
