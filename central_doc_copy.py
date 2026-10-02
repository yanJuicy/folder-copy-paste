from pywinauto import Desktop
import time
import os


# ==================================================
# 설정
# ==================================================

# 프로그램을 처음 실행했을 때의 창 제목
PROGRAM_TITLE = "<하이쎄미코 영업팀>"

# 탐색 시작 위치
ROOT_FOLDER = "<하이쎄미코 영업팀>"

# 로컬에 복제할 위치
LOCAL_ROOT = r"C:\Users\HP\Downloads\test_central"


# ==================================================
# 프로그램 PID
# ==================================================

APP_PID = None


# ==================================================
# 프로그램 창 최초 찾기
# ==================================================

def find_initial_window():

    desktop = Desktop(backend="uia")

    try:

        window = desktop.window(
            title=PROGRAM_TITLE
        )

        if window.exists():

            print(
                f"프로그램 창 발견: {window.window_text()}"
            )

            return window

    except Exception as e:

        print(
            f"프로그램 창 탐색 실패: {e}"
        )

    return None


# ==================================================
# 프로그램 PID 저장
# ==================================================

def initialize_app():

    global APP_PID

    window = find_initial_window()

    if window is None:

        print(
            "프로그램 창을 찾을 수 없습니다."
        )

        return False

    try:

        APP_PID = window.process_id()

        print(
            f"프로그램 PID: {APP_PID}"
        )

        return True

    except Exception as e:

        print(
            f"PID를 가져올 수 없습니다: {e}"
        )

        return False


# ==================================================
# 프로그램 창 다시 찾기
# ==================================================

def get_window():

    global APP_PID

    if APP_PID is None:

        return None

    desktop = Desktop(backend="uia")

    try:

        windows = desktop.windows(
            process=APP_PID
        )

    except Exception:

        return None

    # PID가 같은 창 중 List가 있는 창 찾기
    for window in windows:

        try:

            lists = window.descendants(
                control_type="List"
            )

            if lists:

                return window

        except Exception:

            pass

    # List가 없더라도 PID가 같은 창이 있으면 반환
    if windows:

        return windows[0]

    return None


# ==================================================
# 현재 List 가져오기
# ==================================================

def get_file_list():

    window = get_window()

    if window is None:

        print(
            "프로그램 창을 찾을 수 없습니다."
        )

        return None

    try:

        lists = window.descendants(
            control_type="List"
        )

        if not lists:

            print(
                "List를 찾을 수 없습니다."
            )

            return None

        return lists[0]

    except Exception as e:

        print(
            f"List를 가져오는 중 오류: {e}"
        )

        return None


# ==================================================
# 현재 목록 가져오기
# ==================================================

def get_items():

    file_list = get_file_list()

    # List 자체를 찾지 못한 경우
    if file_list is None:

        return None

    try:

        return file_list.descendants(
            control_type="ListItem"
        )

    except Exception as e:

        print(
            f"목록을 가져오는 중 오류: {e}"
        )

        return None


# ==================================================
# 항목 유형 가져오기
# ==================================================

def get_item_type(item):

    try:

        for child in item.children():

            automation_id = (
                child.element_info.automation_id
            )

            if automation_id == "System.ItemTypeText":

                try:

                    return child.get_value()

                except Exception:

                    return ""

    except Exception:

        pass

    return ""


# ==================================================
# 현재 목록 출력
# ==================================================

def print_items(path):

    items = get_items()

    print()
    print("=" * 70)
    print(f"현재 위치: {path}")
    print("=" * 70)

    # List를 찾지 못한 경우
    if items is None:

        print(
            "현재 폴더의 목록을 가져오지 못했습니다."
        )

        print("=" * 70)

        return None

    # 빈 폴더
    if len(items) == 0:

        print("(빈 폴더)")

    # 항목 출력
    for item in items:

        try:

            name = item.window_text()

            item_type = get_item_type(item)

            if item_type == "파일 폴더":

                print(
                    f"[폴더] {name}"
                )

            else:

                print(
                    f"[파일] {name}"
                )

        except Exception:

            pass

    print("=" * 70)

    return items


# ==================================================
# 현재 화면에서 폴더 찾기
# ==================================================

def find_folder(folder_name):

    items = get_items()

    if items is None:

        return None

    for item in items:

        try:

            name = item.window_text()

            item_type = get_item_type(item)

            if (
                name == folder_name
                and item_type == "파일 폴더"
            ):

                return item

        except Exception:

            pass

    return None


# ==================================================
# 로컬 폴더 생성
# ==================================================

def create_local_folder(path):

    try:

        os.makedirs(
            path,
            exist_ok=True
        )

        print(
            f"[폴더 생성] {path}"
        )

        return True

    except Exception as e:

        print(
            f"[폴더 생성 실패] {path}"
        )

        print(
            f"    오류: {e}"
        )

        return False


# ==================================================
# 로컬 빈 파일 생성
# ==================================================

def create_local_file(path):

    try:

        # 빈 파일 생성
        with open(
            path,
            "wb"
        ):
            pass

        print(
            f"[파일 생성] {path}"
        )

        return True

    except Exception as e:

        print(
            f"[파일 생성 실패] {path}"
        )

        print(
            f"    오류: {e}"
        )

        return False


# ==================================================
# 현재 폴더 구조를 로컬에 복제
# ==================================================

def copy_current_structure(
    items,
    local_path
):

    # 현재 폴더 생성
    if not create_local_folder(local_path):

        return

    # List 자체는 있지만 항목이 없는 경우
    if items is None:

        return

    # 현재 폴더의 항목 처리
    for item in items:

        try:

            name = item.window_text()

            item_type = get_item_type(item)

            # ------------------------------
            # 폴더
            # ------------------------------

            if item_type == "파일 폴더":

                folder_path = os.path.join(
                    local_path,
                    name
                )

                create_local_folder(
                    folder_path
                )

            # ------------------------------
            # 파일
            # ------------------------------

            else:

                file_path = os.path.join(
                    local_path,
                    name
                )

                create_local_file(
                    file_path
                )

        except Exception as e:

            print(
                f"항목 처리 실패: {e}"
            )


# ==================================================
# 폴더 진입
# ==================================================

def enter_folder(folder):

    folder_name = folder.window_text()

    print()
    print(
        f">>> '{folder_name}' 진입"
    )

    try:

        # 폴더 선택
        folder.click_input()

        # 프로그램 창 다시 가져오기
        window = get_window()

        if window is None:

            print(
                "프로그램 창을 찾을 수 없습니다."
            )

            return False

        # Enter로 폴더 진입
        window.set_focus()

        window.type_keys(
            "{ENTER}"
        )

        # 화면 갱신 대기
        time.sleep(0.5)

        print(
            f">>> '{folder_name}' 진입 완료"
        )

        return True

    except Exception as e:

        print(
            f">>> '{folder_name}' 진입 실패"
        )

        print(
            f"    오류: {e}"
        )

        return False


# ==================================================
# 부모 폴더로 돌아가기
# ==================================================

def go_back():

    print(
        "<<< 부모 폴더로 이동"
    )

    window = get_window()

    if window is None:

        print(
            "프로그램 창을 찾을 수 없습니다."
        )

        return False

    try:

        window.set_focus()

        # Alt + Left
        window.type_keys(
            "%{LEFT}"
        )

        time.sleep(0.5)

        print(
            "<<< 부모 폴더 이동 완료"
        )

        return True

    except Exception as e:

        print(
            f"뒤로가기 실패: {e}"
        )

        return False


# ==================================================
# 재귀 탐색 + 로컬 복제
# ==================================================

def scan_folder(
    path,
    local_path
):

    # ------------------------------------------
    # 현재 폴더 목록 가져오기
    # ------------------------------------------

    items = print_items(
        path
    )

    # List 자체를 찾지 못한 경우
    if items is None:

        print(
            "현재 폴더 탐색 실패"
        )

        return

    # ------------------------------------------
    # 현재 폴더 구조를 로컬에 생성
    # ------------------------------------------

    copy_current_structure(
        items,
        local_path
    )

    # ------------------------------------------
    # 하위 폴더 목록 저장
    # ------------------------------------------

    folders = []

    for item in items:

        try:

            name = item.window_text()

            item_type = get_item_type(item)

            if item_type == "파일 폴더":

                folders.append(
                    name
                )

        except Exception:

            pass

    # ------------------------------------------
    # 하위 폴더 하나씩 탐색
    # ------------------------------------------

    for folder_name in folders:

        # 현재 화면에서 폴더 찾기
        target = find_folder(
            folder_name
        )

        if target is None:

            print(
                f"폴더를 찾을 수 없음: {folder_name}"
            )

            continue

        # 폴더 진입
        success = enter_folder(
            target
        )

        if not success:

            continue

        # --------------------------------------
        # 하위 폴더의 로컬 경로
        # --------------------------------------

        child_local_path = os.path.join(
            local_path,
            folder_name
        )

        # --------------------------------------
        # 하위 폴더 재귀 탐색
        # --------------------------------------

        scan_folder(
            path + "\\" + folder_name,
            child_local_path
        )

        # --------------------------------------
        # 탐색 완료 후 부모로 이동
        # --------------------------------------

        go_back()


# ==================================================
# 프로그램 시작
# ==================================================

print()
print(
    "=========================================="
)

print(
    "문서중앙화 탐색 + 로컬 구조 복제 시작"
)

print(
    "=========================================="
)

print(
    f"로컬 복제 위치: {LOCAL_ROOT}"
)

print()


# ==================================================
# 프로그램 초기화
# ==================================================

if not initialize_app():

    print(
        "프로그램 초기화 실패"
    )

    print(
        "탐색을 종료합니다."
    )

else:

    # ------------------------------------------
    # 로컬 루트 폴더 생성
    # ------------------------------------------

    create_local_folder(
        LOCAL_ROOT
    )

    # ------------------------------------------
    # 전체 탐색 시작
    # ------------------------------------------

    scan_folder(
        ROOT_FOLDER,
        LOCAL_ROOT
    )


# ==================================================
# 종료
# ==================================================

print()
print(
    "=========================================="
)

print(
    "탐색 및 복제 종료"
)

print(
    "=========================================="
)