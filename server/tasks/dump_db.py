from __future__ import absolute_import, unicode_literals

import os
import time
from datetime import datetime
from pathlib import Path

import stomp
from loguru import logger
from pydantic import BaseModel, Field
from server.pg_tool import PostgresConnectData, PostgresTool
from server.tasks.app import app


class DumpDataMsg(BaseModel):
    routing_key: str = Field()
    remote: PostgresConnectData = Field()
    target: PostgresConnectData = Field()


@app.task
def dump(req_data: dict):
    data = DumpDataMsg(**req_data)

    try:
        stomp_conn = stomp.Connection(host_and_ports=[("rabbit", 61613)])
        stomp_conn.connect("admin", "adminadmin5200.", wait=True)
    except Exception as e:
        logger.error(f"连接stomp失败：{e}", name="tasks")
        return

    filename = f"tmp_files/{data.remote.db}_{int(time.time() * 1000)}.dump"
    if not Path(filename).parent.exists():
        Path(filename).parent.mkdir()

    # 远端和目标的数据库工具对象
    remote_tool = PostgresTool(data.remote)
    target_tool = PostgresTool(data.target)

    # 目标数据库如果已经存在则重新命名为：目标数据库_年-月-日:时:分:毫秒
    if target_tool.exist_db():
        data.target.db = (
            f"{data.target.db}_{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}"
        )
        target_tool = PostgresTool(data.target)

    def _send_cmd_log(line: str):
        """
        发送日志至前端
        Args:
            line: 日志内容

        Returns:

        """
        stomp_conn.send(f"/queue/dump_{data.routing_key}", line)

    def _dump_done(cmd, success, exit_code):
        """
        导出命令执行完成
        Args:
            cmd:
            success:
            exit_code:

        Returns:

        """
        if exit_code != 0:
            _send_cmd_log("数据库导出失败，导入中断！")
            return

        # 创建数据库
        target_tool.create_db(_out=_send_cmd_log).wait()
        _send_cmd_log(f"\n标数据库 {data.target.db} 创建成功")

        # 执行恢复数据库命令
        _send_cmd_log("数据库导出成功，开始导入，请等待。。。。。。")
        target_tool.restore_db(
            filename, _out=_send_cmd_log, _err=_send_cmd_log, _done=_restore_done
        ).wait()

    def _restore_done(cmd, success, exit_code):
        """
        恢复数据库命令执行完毕
        Args:
            cmd:
            success:
            exit_code:

        Returns:

        """
        if exit_code == 0:
            # noinspection SqlDialectInspection,SqlNoDataSourceInspection
            sql = "DELETE FROM ir_attachment;"
            target_tool.execute_sql(sql).wait()
            _send_cmd_log(f"成功导入至目标数据库 {data.target.db} 中")
            os.remove(filename)

    remote_tool.dump_db(
        filename, _out=_send_cmd_log, _err=_send_cmd_log, _done=_dump_done
    ).wait()
    stomp_conn.disconnect()
