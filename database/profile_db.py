"""
用户档案 SQLite 数据库服务

存储硬件钱包用户基础信息（经验等级、地区、设备型号、常用链、连接方式、
是否开启 Passphrase、是否完成备份验证），用于个性化安全建议和故障排查。
"""

import sqlite3
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from utils.logger_handler import logger


@dataclass
class UserProfile:
    """硬件钱包用户档案数据结构"""
    user_id: str
    experience_level: Optional[str] = None   # 新手 / 进阶 / 资深
    region: Optional[str] = None             # 地区
    device_model: Optional[str] = None       # KeyGuard 型号
    preferred_chains: Optional[str] = None   # 常用链，如 "BTC, ETH, SOL"
    connection_method: Optional[str] = None  # USB-C / 蓝牙
    passphrase_enabled: Optional[bool] = None
    backup_verified: Optional[bool] = None


class ProfileDatabase:
    """硬件钱包用户档案数据库服务"""

    def __init__(self, db_path: str = "data/profiles.db"):
        """
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        expected_columns = {
            "user_id",
            "experience_level",
            "region",
            "device_model",
            "preferred_chains",
            "connection_method",
            "passphrase_enabled",
            "backup_verified",
            "updated_at",
        }
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'user_profiles'
        """)
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(user_profiles)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if not expected_columns.issubset(existing_columns):
                logger.info("[ProfileDB] 检测到旧版用户档案表，重建为硬件钱包档案结构")
                cursor.execute("DROP TABLE user_profiles")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                experience_level TEXT,
                region TEXT,
                device_model TEXT,
                preferred_chains TEXT,
                connection_method TEXT,
                passphrase_enabled BOOLEAN,
                backup_verified BOOLEAN,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"[ProfileDB] 数据库初始化完成: {self.db_path}")

    def save_profile(self, profile: UserProfile) -> bool:
        """保存或更新用户档案

        Args:
            profile: 用户档案对象

        Returns:
            是否保存成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles
                (user_id, experience_level, region, device_model,
                 preferred_chains, connection_method, passphrase_enabled, backup_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                profile.experience_level,
                profile.region,
                profile.device_model,
                profile.preferred_chains,
                profile.connection_method,
                profile.passphrase_enabled,
                profile.backup_verified,
            ))

            conn.commit()
            conn.close()
            logger.info(f"[ProfileDB] 用户档案已保存: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"[ProfileDB] 保存失败: {e}")
            return False

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户档案

        Args:
            user_id: 用户 ID

        Returns:
            用户档案对象，不存在则返回 None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, experience_level, region, device_model,
                       preferred_chains, connection_method, passphrase_enabled, backup_verified
                FROM user_profiles WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return UserProfile(
                    user_id=row[0],
                    experience_level=row[1],
                    region=row[2],
                    device_model=row[3],
                    preferred_chains=row[4],
                    connection_method=row[5],
                    passphrase_enabled=bool(row[6]) if row[6] is not None else None,
                    backup_verified=bool(row[7]) if row[7] is not None else None,
                )
            return None
        except Exception as e:
            logger.error(f"[ProfileDB] 查询失败: {e}")
            return None
