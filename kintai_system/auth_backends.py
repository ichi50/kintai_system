# kintai_system/auth_backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

try:
    from common.models import mst_employee
except ImportError:
    # 従業員モデルが見つからない場合のフォールバック（環境に合わせてパスを修正してください）
    mst_employee = None

UserModel = get_user_model()

class EmployeeIdOrEmailBackend(ModelBackend):
    """
    ユーザー名ではなく、社員番号またはメールアドレスで認証を行うカスタムバックエンド。
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
            
        search_term = username # 入力された値（社員番号かメールアドレス）
        
        # 1. ユーザーを検索
        try:            
            # メールアドレス形式の簡易判定
            if '@' in search_term and '.' in search_term:
                # ユーザーモデルで直接メールアドレスを検索
                user = mst_employee.objects.get(emp_email__iexact=search_term)
            
            # 社員番号検索（MstEmployee が存在する場合のみ）
            elif mst_employee:
                # MstEmployee で社員番号を検索し、関連付けられた Django User を取得
                employee = mst_employee.objects.get(employee__iexact=search_term)
                user = employee.user
            
            else:
                # どちらの形式でもない、または MstEmployee がない場合は認証失敗
                return None
                
        except (UserModel.DoesNotExist, mst_employee.DoesNotExist):
            # ユーザーが見つからない
            return None
        except Exception:
            # その他のデータベースエラーなど
            return None

        # 2. パスワードの検証
        if user.check_password(password) and self.user_can_authenticate(user):
            # 認証成功
            return user
        
        # パスワード不一致
        return None

    def get_user(self, user_id):
        """セッションIDからユーザーを取得するのに必要"""
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None