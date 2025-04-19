import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QButtonGroup
from PyQt5.QtCore import Qt
from menu_planner_ui import Ui_MainWindow
from menu_data import menu_database
from motivasi import motivational_messages

class MenuPlannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())  

        with open("style.qss", "r") as f:
            self.setStyleSheet(f.read())

        self.meal_group = QButtonGroup(self)
        self.meal_group.addButton(self.ui.sarapan_2, 1)
        self.meal_group.addButton(self.ui.siang_2, 2)
        self.meal_group.addButton(self.ui.malam_2, 3)
        self.meal_group.addButton(self.ui.snack_2, 4)
        self.meal_group.addButton(self.ui.all_2, 5)

        self.ui.start.clicked.connect(self.show_input_page)
        self.ui.level_2.setMinimum(1)
        self.ui.level_2.setMaximum(3)
        self.ui.level_2.valueChanged.connect(self.update_slider_value)
        self.ui.generate_2.clicked.connect(self.generate_menu)
        self.ui.surprise_2.clicked.connect(self.surprise_menu)
        self.ui.reset.clicked.connect(self.reset_fields)

        for widget in [
            self.ui.user_2, self.ui.mood_2, self.ui.manis_2, self.ui.asin_2,
            self.ui.pedas_2, self.ui.asam_2, self.ui.sarapan_2, self.ui.siang_2,
            self.ui.malam_2, self.ui.snack_2, self.ui.all_2,
            self.ui.level_2, self.ui.tujuan_2
        ]:
            widget.installEventFilter(self)

        self.ui.stackedWidget.setCurrentIndex(0)
        self.update_slider_value()

    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress or event.type() == event.KeyPress:
            self.ui.surprise_2.setEnabled(False)
        return super().eventFilter(obj, event)

    def show_input_page(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def update_slider_value(self):
        self.ui.val_level_2.setText(str(self.ui.level_2.value()))

    def get_selected_flavors(self):
        flavors = []
        if self.ui.manis_2.isChecked(): flavors.append("Manis")
        if self.ui.asin_2.isChecked(): flavors.append("Asin")
        if self.ui.pedas_2.isChecked(): flavors.append("Pedas")
        if self.ui.asam_2.isChecked(): flavors.append("Asam")
        return flavors

    def get_selected_meal_time(self):
        meal_id = self.meal_group.checkedId()
        return {
            1: "Sarapan",
            2: "Makan Siang",
            3: "Makan Malam",
            4: "Snack",
            5: "Sarapan - Makan Malam"
        }.get(meal_id)

    def get_menu_options(self, meal_time, flavors, level, goal):
        kategori_data = menu_database.get(meal_time, {})
        options = set()
        fallback_used = False
        used_flavor_label = ""
        reason = ""

        if len(flavors) == 2:
            combo_key = "".join(sorted(flavors))
            flavor_data = kategori_data.get(combo_key, {})
            if flavor_data:
                used_flavor_label = " + ".join(sorted(flavors))
                options.update(flavor_data.get(level, []))  
                if not options and goal != "Random":
                    options.update(flavor_data.get(goal, []))  

        if not options:
            for rasa in flavors:
                flavor_data = kategori_data.get(rasa, {})
                if flavor_data:
                    if not used_flavor_label:
                        used_flavor_label = rasa
                    else:
                        used_flavor_label += f" + {rasa}"
                    options.update(flavor_data.get(level, []))  
                    if not options and goal != "Random":
                        options.update(flavor_data.get(goal, []))

        if not options:
            fallback_used = True
            used_flavor_label = "Random"
            if "Pedas" in flavors and meal_time == "Sarapan":
                reason = "Rasa pedas kurang cocok untuk sarapan karena bisa mengganggu pencernaan."
            elif "Asam" in flavors and meal_time == "Sarapan":
                reason = "Rasa asam di pagi hari bisa memicu maag bagi sebagian orang."
            else:
                reason = "Kombinasi rasa yang dipilih belum tersedia di database."

            for flavor in ["Manis", "Asin"]:
                flavor_data = kategori_data.get(flavor, {})
                options.update(flavor_data.get(level, []))
                if not options and goal != "Random":
                    options.update(flavor_data.get(goal, []))

        if not options:
            for flavor_data in kategori_data.values():
                for menu_list in flavor_data.values():
                    options.update(menu_list)

        return list(options), used_flavor_label, fallback_used, reason

    def generate_menu(self):
        name = self.ui.user_2.text().strip()
        mood = self.ui.mood_2.currentText()
        flavors = self.get_selected_flavors()
        meal_time = self.get_selected_meal_time()
        level = self.ui.level_2.value()
        goal = self.ui.tujuan_2.currentText()

        if not name or mood == "- Pilih -" or not flavors or not meal_time:
            QMessageBox.warning(self, "Input Error", "Isi semua input dengan benar!")
            return
        if len(flavors) > 2:
            QMessageBox.warning(self, "Input Error", "Pilih maksimal dua rasa!")
            return
        if goal == "- Pilih -":
            QMessageBox.warning(self, "Input Error", "Isi semua input dengan benar!")
            return

        result_text = f"🍽️ Menu Rekomendasi Hari Ini untuk {name}\n"
        result_text += "────────────────────────────────────────────────\n"
        meal_times = ["Sarapan", "Makan Siang", "Makan Malam", "Snack"] if meal_time == "Sarapan - Makan Malam" else [meal_time]

        for mt in meal_times:
            options, used_flavor_label, fallback_used, reason = self.get_menu_options(mt, flavors, level, goal)

            emoji = {
                "Sarapan": "🍳",
                "Makan Siang": "🍛",
                "Makan Malam": "🍲",
                "Snack": "🍪"
            }.get(mt, "🍽️")

            result_text += f"{emoji} {mt} (Rasa: {used_flavor_label}):\n"

            if reason:
                result_text += f"⚠️ Catatan: {reason}\n"
                QMessageBox.information(self, "Catatan Kesehatan", reason)

            menu = random.choice(options) if options else "Tidak ada menu cocok 🥲"
            tag = " (Alternatif)" if fallback_used else ""
            result_text += f"{menu}{tag}\n"

        self.ui.result.setText(result_text)
        messages = motivational_messages.get(mood, ["Semangat ya!"])
        QMessageBox.information(self, "Motivasi Harian", random.choice(messages))

    def surprise_menu(self):
        name = self.ui.user_2.text().strip() or "User"
        result_text = f"🎉 Menu Surprise Hari Ini untuk {name}\n"
        result_text += "────────────────────────────────────────────────\n"

        meal_times = ["Sarapan", "Makan Siang", "Makan Malam", "Snack"]
        flavors = ["Manis", "Asin", "Pedas", "Asam"]
        levels = [1, 2, 3]
        goals = ["Diet", "Hemat", "Fancy"]

        for mt in meal_times:
            random_flavors = random.sample(flavors, k=random.randint(1, 2))
            level = random.choice(levels)
            goal = random.choice(goals)

            options, used_flavor_label, fallback_used, reason = self.get_menu_options(mt, random_flavors, level, goal)

            emoji = {
                "Sarapan": "🍳",
                "Makan Siang": "🍛",
                "Makan Malam": "🍲",
                "Snack": "🍪"
            }.get(mt, "🍽️")

            result_text += f"{emoji} {mt} (Rasa: {used_flavor_label}):\n"
            if reason:
                result_text += f"⚠️ Catatan: {reason}\n"

            menu = random.choice(options) if options else "Random surprise dish!"
            result_text += f"{menu}\n"

        self.ui.result.setText(result_text)
        messages = motivational_messages["Surprise"]
        QMessageBox.information(self, "Motivasi Harian", random.choice(messages))

    def reset_fields(self):
        confirm = QMessageBox.question(
            self,
            "Konfirmasi Reset",
            "Yakin ingin menghapus semua input dan hasil?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.No:
            return 

        self.ui.user_2.clear()
        self.ui.mood_2.setCurrentIndex(0)
        self.ui.tujuan_2.setCurrentIndex(0)

        self.ui.manis_2.setChecked(False)
        self.ui.asin_2.setChecked(False)
        self.ui.pedas_2.setChecked(False)
        self.ui.asam_2.setChecked(False)

        self.meal_group.setExclusive(False)
        for btn in self.meal_group.buttons():
            btn.setChecked(False)
        self.meal_group.setExclusive(True)

        self.ui.level_2.setValue(1)
        self.ui.result.clear()
        self.ui.surprise_2.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MenuPlannerApp()
    window.show()
    sys.exit(app.exec_())