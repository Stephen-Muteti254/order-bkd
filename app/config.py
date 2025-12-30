class Config:
    SQLALCHEMY_DATABASE_URI = (
        "postgresql+psycopg://buxton:bTP51pT1eYjCgbQ_APOSnw@"
        "order-mgt-19894.j77.aws-ap-south-1.cockroachlabs.cloud:26257/"
        "order-mgt"
        "?sslmode=verify-full"
        "&sslrootcert=certs/root.crt"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
