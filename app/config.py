class Config:
    SQLALCHEMY_DATABASE_URI = (
        "cockroachdb+psycopg://buxton:UeNJ_CgmYh9NhU4hRH9_dw@"
        "order-mgt-19894.j77.aws-ap-south-1.cockroachlabs.cloud:26257/"
        "order-mgt"
        "?sslmode=verify-full"
        "&sslrootcert=certs/root.crt"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
