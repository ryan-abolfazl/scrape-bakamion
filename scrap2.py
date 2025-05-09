from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import time
import random
import csv
import os
import pandas as pd
import openpyxl


# تنظیمات
xpath_click_target = '//*[@id="get_seller_phone"]'
# batch_size = 1
delay_between = (1, 3)
max_consecutive_errors = 5


def extract_ad_links():
    print("📥 در حال جمع‌آوری لینک‌های آگهی از صفحه اصلی...")
    driver = Firefox()
    driver.get("https://bakamion.ir/ads")
    time.sleep(3)

    # فقط یک‌بار اسکرول تا پایین
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(25)

    # گرفتن HTML کامل صفحه بعد از اسکرول
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # استخراج لینک‌ها
    ad_links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        # print(href)
        if re.match("https://bakamion.ir/ad/", href):
            ad_links.add(href)

    sorted_links = sorted(ad_links, reverse=True)
    links = [link for link in sorted_links if "create" not in link]
    print(f" آگهی پیدا شد{len(links)}")
    return links


def crawl_ad(link, csv_writer):
    url = link
    print(f"🔍 در حال پردازش آگهی: {url}")
    try:
        driver = Firefox()
        driver.get(url)
        time.sleep(3)

        try:
            btn = driver.find_element(By.XPATH, xpath_click_target)
            btn.click()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ دکمه کلیک نشد: {e}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        name_tag = soup.find("span", class_="fs-6 fs-lg-5 fw-bold text-dark")
        name = name_tag.text.strip() if name_tag else "بدون عنوان"

        labels = soup.find_all("div", class_="col-4 col-lg-3 fs-7 fs-lg-6 text-body-secondary fw-normal")
        values = soup.find_all("div", class_="d-flex justify-content-end justify-content-lg-start align-items-center col-8 col-lg-9 fs-7 fs-lg-6 text-body fw-bold")

        info_dict = {}
        for label_tag, value_tag in zip(labels, values):
            label = label_tag.text.strip()
            value = value_tag.text.strip()
            info_dict[label] = value

        # استخراج داده‌های مورد نظر
        city = info_dict.get("استان", "")
        year = info_dict.get("سال", "")
        raw_phone = info_dict.get("قیمت", "")
        match = re.search(r'\d{10}', raw_phone)
        phone = match.group() if match else ""

        # نوشتن در فایل CSV
        csv_writer.writerow([name, city, year, phone])

        print("✅", name)
        print(info_dict)
        print("-" * 40)
        return True

    except Exception as e:
        print(f"❗ خطا در پردازش آگهی {url}: {e}")
        return False

def crawl_batch():
    urls = extract_ad_links()
    if urls is None:
        print("⛔ برنامه متوقف شد.")
        return

    # 🔸 آماده‌سازی فایل CSV
    file_exists = os.path.exists("output1.csv")
    csv_file = open("output1.csv", "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if not file_exists:
        csv_writer.writerow(["نام", "شهر", "سال ساخت", "شماره تماس"])

    not_found = 0
    found = 0
    # max_founds = 2
    for link in urls:
        success = crawl_ad(link, csv_writer)
        if not success:
            not_found += 1
            if not_found >= max_consecutive_errors:
                print("⏸ توقف ۶۰ ثانیه‌ای به دلیل خطاهای پیاپی.")
                time.sleep(60)
                not_found = 0
        else:
            not_found = 0
            found += 1
            if found == 3:
                break


        time.sleep(random.uniform(*delay_between))

    csv_file.close()
    print("📁 خروجی در فایل output1.csv ذخیره شد.")
    df = pd.read_csv("output1.csv", encoding="utf-8")
    df.to_excel("output1.xlsx", index=False)
    print("📁 خروجی در فایل output1.xlsx ذخیره شد.")


# اجرای برنامه
crawl_batch()