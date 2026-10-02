from pywinauto import Desktop
import time
import os
import json


# ============================================================
# 설정
# ============================================================

# 실제 문서중앙화 프로그램의 창 제목
# < > 는 넣지 않습니다.
PROGRAM_TITLE = "99_교육자료"

# 탐색 시작 위치의 이름
ROOT_FOLDER = "99_교육자료"

# 로컬에 복제할 위치
LOCAL_ROOT = r"C:\Users\HP\Downloads\test_central"

# JSON 파일 저장 위치
JSON_FILE = r"C:\Users\HP\Downloads\sales_team_structure.json"

# 문서중앙화 프로그램 PID
APP_PID = None


# ============================================================
# 프로그램 초기 창 찾기
# ============================================================

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


# ============================================================
# 프로그램 초기화
# ============================================================

def initialize_app():

    global APP_PID

    window = find_initial_window()

    if window is None:

        print("프로그램 창을 찾을 수 없습니다.")

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


# ============================================================
# 현재 문서중앙화 창 가져오기
# ============================================================

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

    # PID가 같은 창 중 List를 가지고 있는 창을 찾음
    for window in windows:

        try:

            lists = window.descendants(
                control_type="List"
            )

            if lists:

                return window

        except Exception:

            pass

    # List를 가진 창을 못 찾았을 경우
    if windows:

        return windows[0]

    return None


# ============================================================
# 현재 파일 목록 가져오기
# ============================================================

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


# ============================================================
# 현재 폴더의 항목 가져오기
# ============================================================

def get_items():

    file_list = get_file_list()

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


# ============================================================
# 폴더 / 파일 종류 확인
#
# 확장자를 사용하지 않음
#
# System.ItemTypeText
#     "파일 폴더"
#     "MP4 파일"
#     "Excel 파일"
#     ...
# ============================================================

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


# ============================================================
# 현재 폴더 목록 출력
# ============================================================

def print_items(path):

    items = get_items()

    print()
    print("=" * 70)
    print(
        f"현재 위치: {path}"
    )
    print("=" * 70)

    if items is None:

        print(
            "현재 폴더의 목록을 가져오지 못했습니다."
        )

        print("=" * 70)

        return None

    if len(items) == 0:

        print("(빈 폴더)")

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


# ============================================================
# 현재 화면에서 특정 폴더 찾기
# ============================================================

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


# ============================================================
# 로컬 폴더 생성
# ============================================================

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


# ============================================================
# 로컬 빈 파일 생성
# ============================================================

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


# ============================================================
# 문서중앙화 폴더 진입
# ============================================================

def enter_folder(folder):

    folder_name = folder.window_text()

    print()
    print(
        f">>> '{folder_name}' 진입"
    )

    try:

        # 폴더 선택
        folder.click_input()

        # 프로그램 창 가져오기
        window = get_window()

        if window is None:

            print(
                "프로그램 창을 찾을 수 없습니다."
            )

            return False

        # 창 활성화
        window.set_focus()

        # Enter로 폴더 진입
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


# ============================================================
# 부모 폴더로 이동
# ============================================================

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

        # 화면 갱신 대기
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


# ============================================================
# 현재 폴더 탐색
#
# 이 함수에서 동시에 수행:
#
# 1. 문서중앙화 탐색
# 2. 로컬 폴더 생성
# 3. 로컬 빈 파일 생성
# 4. JSON 구조 생성
# 5. 하위 폴더 재귀 탐색
# ============================================================

def scan_folder(
    path,
    local_path,
    structure_node
):

    # --------------------------------------------------------
    # 현재 폴더의 항목 가져오기
    # --------------------------------------------------------

    items = print_items(path)

    if items is None:

        print(
            "현재 폴더 탐색 실패"
        )

        return

    # --------------------------------------------------------
    # 현재 로컬 폴더 생성
    # --------------------------------------------------------

    create_local_folder(
        local_path
    )

    # --------------------------------------------------------
    # JSON children 초기화
    # --------------------------------------------------------

    structure_node["children"] = []

    # 하위 폴더 목록
    folders = []

    # --------------------------------------------------------
    # 현재 폴더의 모든 항목 처리
    # --------------------------------------------------------

    for item in items:

        try:

            name = item.window_text()

            item_type = get_item_type(item)

            # =================================================
            # 폴더
            # =================================================

            if item_type == "파일 폴더":

                # ---------------------------------------------
                # JSON에 폴더 등록
                # ---------------------------------------------

                folder_node = {

                    "name": name,

                    "type": "folder",

                    "children": []

                }

                structure_node[
                    "children"
                ].append(
                    folder_node
                )

                # ---------------------------------------------
                # 나중에 실제 폴더 진입을 위해 저장
                # ---------------------------------------------

                folders.append(
                    (
                        name,
                        folder_node
                    )
                )

                # ---------------------------------------------
                # 로컬 폴더 생성
                # ---------------------------------------------

                local_folder_path = os.path.join(
                    local_path,
                    name
                )

                create_local_folder(
                    local_folder_path
                )

            # =================================================
            # 파일
            # =================================================

            else:

                # ---------------------------------------------
                # JSON에 파일 등록
                # ---------------------------------------------

                file_node = {

                    "name": name,

                    "type": "file"

                }

                structure_node[
                    "children"
                ].append(
                    file_node
                )

                # ---------------------------------------------
                # 로컬에 빈 파일 생성
                # ---------------------------------------------

                local_file_path = os.path.join(
                    local_path,
                    name
                )

                create_local_file(
                    local_file_path
                )

        except Exception as e:

            print(
                f"항목 처리 실패: {e}"
            )

    # ========================================================
    # 하위 폴더 재귀 탐색
    # ========================================================

    for folder_name, folder_node in folders:

        # ----------------------------------------------------
        # 현재 화면에서 폴더 다시 찾기
        # ----------------------------------------------------

        target = find_folder(
            folder_name
        )

        if target is None:

            print(
                f"폴더를 찾을 수 없음: {folder_name}"
            )

            continue

        # ----------------------------------------------------
        # 폴더 진입
        # ----------------------------------------------------

        success = enter_folder(
            target
        )

        if not success:

            continue

        # ----------------------------------------------------
        # 로컬 하위 경로
        # ----------------------------------------------------

        child_local_path = os.path.join(
            local_path,
            folder_name
        )

        # ----------------------------------------------------
        # 문서중앙화 논리 경로
        # ----------------------------------------------------

        child_path = (
            path
            + "\\"
            + folder_name
        )

        # ----------------------------------------------------
        # 재귀 탐색
        # ----------------------------------------------------

        scan_folder(

            child_path,

            child_local_path,

            folder_node

        )

        # ----------------------------------------------------
        # 부모 폴더로 복귀
        # ----------------------------------------------------

        go_back()


# ============================================================
# JSON 파일 저장
# ============================================================

def save_json(structure):

    print()
    print(
        "JSON 파일 생성 중..."
    )

    try:

        with open(
            JSON_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                structure,
                f,
                ensure_ascii=False,
                indent=4
            )

        print(
            f"JSON 생성 완료: {JSON_FILE}"
        )

        return True

    except Exception as e:

        print(
            f"JSON 생성 실패: {e}"
        )

        return False


# ============================================================
# 메인 실행
# ============================================================

print()
print(
    "=========================================="
)

print(
    "문서중앙화 탐색 + 로컬 구조 복제 + JSON 생성"
)

print(
    "=========================================="
)

print(
    f"로컬 복제 위치: {LOCAL_ROOT}"
)

print(
    f"JSON 저장 위치: {JSON_FILE}"
)

print()


# ============================================================
# 프로그램 초기화
# ============================================================

if not initialize_app():

    print(
        "프로그램 초기화 실패"
    )

    print(
        "탐색을 종료합니다."
    )

else:

    # --------------------------------------------------------
    # JSON 최상위 구조
    # --------------------------------------------------------

    DOCUMENT_STRUCTURE = {

        "name": ROOT_FOLDER,

        "type": "folder",

        "children": []

    }

    # --------------------------------------------------------
    # 로컬 루트 생성
    # --------------------------------------------------------

    create_local_folder(
        LOCAL_ROOT
    )

    # --------------------------------------------------------
    # 전체 탐색
    #
    # 문서중앙화
    #     ↓
    # 로컬 구조 복제
    #     ↓
    # JSON 구조 생성
    # --------------------------------------------------------

    scan_folder(

        ROOT_FOLDER,

        LOCAL_ROOT,

        DOCUMENT_STRUCTURE

    )

    # --------------------------------------------------------
    # JSON 저장
    # --------------------------------------------------------

    save_json(
        DOCUMENT_STRUCTURE
    )


# ============================================================
# 종료
# ============================================================

print()
print(
    "=========================================="
)

print(
    "탐색 / 복제 / JSON 생성 종료"
)

print(
    "=========================================="
)