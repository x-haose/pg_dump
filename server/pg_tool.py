import sh
from pydantic import BaseModel, Field

from server.log import get_log


class PostgresConnectData(BaseModel):
    """
    PostgreSQL数据库连接参数
    """

    db: str = Field(title="数据库名字")
    host: str = Field(title="数据库IP")
    port: str = Field(title="数据库端口号")
    user: str = Field(title="数据库用户名")
    passwd: str = Field(title="数据库密码")


class PostgresTool(object):
    """
    PostgreSQL 常用工具
    """

    def __init__(self, connect_data: PostgresConnectData):
        self.connect_data = connect_data

    def create_db(self, **kwargs):
        """
        创建数据库
        Returns:

        """
        args = (
            "-h",
            self.connect_data.host,
            "-p",
            self.connect_data.port,
            "-U",
            self.connect_data.user,
            self.connect_data.db,
        )

        pg_sh = sh.Command("createdb")
        kwargs["_in"] = self.connect_data.passwd
        return pg_sh(*args, **kwargs)

    def exist_db(self):
        """
        返回数据库是否存在
        Returns:

        """
        # noinspection SqlDialectInspection,SqlNoDataSourceInspection
        sql = f"SELECT u.datname FROM pg_catalog.pg_database u where u.datname='{self.connect_data.db}';"
        result = self.execute_sql(sql, use_db=False)
        return self.connect_data.db in result.stdout.decode()

    def execute_sql(self, sql, use_db=True, **kwargs):
        """
        执行sql
        Args:
            sql: 要执行的sql
            use_db: 是否使用数据库执行
            **kwargs:

        Returns:

        """
        args = [
            "-h",
            self.connect_data.host,
            "-p",
            self.connect_data.port,
            "-U",
            self.connect_data.user,
            "-c",
            sql,
        ]
        if use_db:
            args.extend(
                [
                    "-d",
                    self.connect_data.db,
                ]
            )
        pg_sh = sh.Command("psql")
        kwargs["_in"] = self.connect_data.passwd
        return pg_sh(*args, **kwargs)

    def dump_db(self, filename: str, **kwargs):
        """
        导出数据库
        Args:
            filename: 导出的文件名

        Returns:

        """
        args = (
            "-h",
            self.connect_data.host,
            "-p",
            self.connect_data.port,
            "-U",
            self.connect_data.user,
            "-d",
            self.connect_data.db,
            "-v",
            "-W",
            "-Fc",
            "-n",
            "public",
            "--no-tablespaces",
            "-f",
            filename,
        )
        pg_sh = sh.Command("pg_dump")

        kwargs["_in"] = self.connect_data.passwd
        return pg_sh(*args, **kwargs)

    def restore_db(self, filename: str, **kwargs):
        """
        恢复数据库
        Args:
            filename: 导入的文件名

        Returns:

        """
        jobs = int(sh.Command("nproc")())
        args = (
            "-h",
            self.connect_data.host,
            "-p",
            self.connect_data.port,
            "-U",
            self.connect_data.user,
            "-d",
            self.connect_data.db,
            "-n",
            "public",
            "-W",
            "-Fc",
            "-j",
            jobs,
            filename,
        )
        pg_sh = sh.Command("pg_restore")
        kwargs["_in"] = self.connect_data.passwd
        return pg_sh(*args, **kwargs)


def test():
    connect_data = PostgresConnectData(
        host="127.0.0.1", port="5432", user="postgres", passwd="123456", db="sale"
    )
    tool = PostgresTool(connect_data)
    is_exist = tool.exist_db()
    tool_logger.info(f"数据库是否存在：{is_exist}")
    if not is_exist:
        tool.create_db()
    else:

        def out(line):
            print(line)

        def done(cmd, success, exit_code):
            print(f"完成: {exit_code}")

        tool.dump_db("011.dump", _out=out, _err=out, _done=done).wait()


if __name__ == "__main__":
    tool_logger = get_log("pg_tool")
    test()
