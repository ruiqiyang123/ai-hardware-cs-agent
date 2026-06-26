"""
用户档案 SQLite 数据库服务

存储用户基础信息（年龄、地址、家庭面积、是否有宠物、是否有地毯、设备型号），
用于个性化推荐和故障排查。
"""

import sqlite3
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from utils.logger_handler import logger


@dataclass
class UserProfile:
    """用户档案数据结构"""
    user_id: str
    age: Optional[int] = None
    address: Optional[str] = None
    home_area: Optional[float] = None  # 平方米
    has_pets: Optional[bool] = None
    has_carpets: Optional[bool] = None
    device_model: Optional[str] = None


class ProfileDatabase:
    """用户档案数据库服务"""

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                age INTEGER,
                address TEXT,
                home_area REAL,
                has_pets BOOLEAN,
                has_carpets BOOLEAN,
                device_model TEXT,
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
                (user_id, age, address, home_area, has_pets, has_carpets, device_model)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                profile.age,
                profile.address,
                profile.home_area,
                profile.has_pets,
                profile.has_carpets,
                profile.device_model
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
                SELECT user_id, age, address, home_area, has_pets, has_carpets, device_model
                FROM user_profiles WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return UserProfile(
                    user_id=row[0],
                    age=row[1],
                    address=row[2],
                    home_area=row[3],
                    has_pets=bool(row[4]) if row[4] is not None else None,
                    has_carpets=bool(row[5]) if row[5] is not None else None,
                    device_model=row[6]
                )
            return None
        except Exception as e:
            logger.error(f"[ProfileDB] 查询失败: {e}")
            return None
