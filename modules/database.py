import sqlite3
import os
from datetime import datetime
import json

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path="pregnancy_records.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 기록 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                image_path TEXT NOT NULL,
                result TEXT,
                gestational_age TEXT,
                gender TEXT,
                hospital TEXT,
                measurements TEXT,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_record(self, record_data):
        """기록 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 데이터 준비
        analysis_date = record_data.get('analysis_date', datetime.now().isoformat())
        
        cursor.execute('''
            INSERT INTO records (
                type, analysis_date, image_path, result, 
                gestational_age, gender, hospital, measurements, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_data.get('type'),
            analysis_date,
            record_data.get('image_path'),
            record_data.get('result'),
            record_data.get('gestational_age'),
            record_data.get('gender'),
            record_data.get('hospital'),
            record_data.get('measurements'),
            record_data.get('memo')
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_records(self, filter_type="전체", sort_order="최신순"):
        """기록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 기본 쿼리
        query = "SELECT * FROM records"
        params = []
        
        # 타입 필터
        if filter_type != "전체":
            type_map = {
                "임신테스트기": "pregnancy_test",
                "초음파": "ultrasound"
            }
            if filter_type in type_map:
                query += " WHERE type = ?"
                params.append(type_map[filter_type])
        
        # 정렬
        if sort_order == "최신순":
            query += " ORDER BY analysis_date DESC"
        else:
            query += " ORDER BY analysis_date ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 딕셔너리 형태로 변환
        columns = [description[0] for description in cursor.description]
        records = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return records
    
    def get_record_by_id(self, record_id):
        """ID로 특정 기록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            record = dict(zip(columns, row))
        else:
            record = None
        
        conn.close()
        return record
    
    def update_record(self, record_id, record_data):
        """기록 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 업데이트할 필드들 구성
        fields = []
        params = []
        
        for key, value in record_data.items():
            if key != 'id':
                fields.append(f"{key} = ?")
                params.append(value)
        
        if fields:
            query = f"UPDATE records SET {', '.join(fields)} WHERE id = ?"
            params.append(record_id)
            
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def delete_record(self, record_id):
        """기록 삭제"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 먼저 이미지 파일 경로 가져오기
        cursor.execute("SELECT image_path FROM records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            image_path = row[0]
            # 이미지 파일도 삭제 (선택적)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # 파일 삭제 실패해도 DB 레코드는 삭제
        
        # DB 레코드 삭제
        cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """통계 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # 전체 기록 수
        cursor.execute("SELECT COUNT(*) FROM records")
        stats['total_records'] = cursor.fetchone()[0]
        
        # 타입별 기록 수
        cursor.execute("SELECT type, COUNT(*) FROM records GROUP BY type")
        type_counts = cursor.fetchall()
        stats['by_type'] = {row[0]: row[1] for row in type_counts}
        
        # 최근 기록
        cursor.execute("SELECT * FROM records ORDER BY analysis_date DESC LIMIT 5")
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        stats['recent_records'] = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return stats
    
    def search_records(self, search_term):
        """기록 검색"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM records 
            WHERE memo LIKE ? 
               OR result LIKE ? 
               OR hospital LIKE ?
               OR gestational_age LIKE ?
            ORDER BY analysis_date DESC
        '''
        
        search_pattern = f"%{search_term}%"
        params = [search_pattern] * 4
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        records = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return records
    
    def backup_database(self, backup_path):
        """데이터베이스 백업"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"백업 실패: {e}")
            return False
    
    def restore_database(self, backup_path):
        """데이터베이스 복원"""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            print(f"복원 실패: {e}")
            return False
