import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

pragma ComponentBehavior: Bound

Window {
    id: root
    width: 480
    height: mainCol.implicitHeight + 44
    minimumWidth: 480
    maximumWidth: 480
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    visible: true
    title: "Discord Image Grabber"

    Component.onCompleted: {
        tokenField.text = backend.savedToken
    }

    // ── Сигналы от бэкенда ────────────────────────────────────────────────────
    Connections {
        target: backend
        function onCloseRequested()      { Qt.quit() }
        function onHideWindow()          { root.hide() }
        function onShowWindow()          { root.show(); root.raise(); root.requestActivate() }
        function onErrorMessage(msg)     { errorPopup.message = msg; errorPopup.open() }
    }

    // ── Диалог ошибки ─────────────────────────────────────────────────────────
    Popup {
        id: errorPopup
        property string message: ""

        x: Math.round((root.width  - width)  / 2)
        y: Math.round((root.height - height) / 2)
        width: 320
        padding: 24
        modal: true
        closePolicy: Popup.NoAutoClose

        background: Rectangle {
            color: backend.colors.bg_dialog
            radius: 8
        }

        Overlay.modal: Rectangle {
            color: backend.colors.overlay
        }

        contentItem: ColumnLayout {
            spacing: 0
            width: errorPopup.width - 48

            Rectangle {
                width: 56; height: 56; radius: 28
                color: backend.colors.bg_err_icon
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 16

                Text {
                    anchors.centerIn: parent
                    text: "!"
                    color: backend.colors.err_icon
                    font { pixelSize: 28; weight: Font.Bold; family: "Segoe UI" }
                }
            }

            Text {
                Layout.fillWidth: true
                text: backend.strings.warning
                color: backend.colors.text_primary
                font { pixelSize: 16; weight: Font.Bold; family: "Segoe UI" }
                horizontalAlignment: Text.AlignHCenter
                Layout.bottomMargin: 10
            }

            Text {
                Layout.fillWidth: true
                text: errorPopup.message
                color: backend.colors.text_secondary
                font { pixelSize: 13; family: "Segoe UI" }
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.bottomMargin: 24
            }

            Rectangle {
                Layout.fillWidth: true
                height: 40
                radius: 4
                color: okBtn.pressed       ? backend.colors.accent_pressed
                     : okBtn.containsMouse ? backend.colors.accent_hover
                     : backend.colors.accent

                MouseArea {
                    id: okBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: errorPopup.close()
                }

                Text {
                    anchors.centerIn: parent
                    text: "OK"
                    color: "#ffffff"
                    font { pixelSize: 14; weight: Font.DemiBold; family: "Segoe UI" }
                }
            }
        }
    }

    // ── Основной контейнер ────────────────────────────────────────────────────
    Rectangle {
        id: card
        anchors.fill: parent
        color: backend.colors.bg_card
        radius: 8

        // Перетаскивание за нон-интерактивные части окна
        DragHandler {
            target: null
            grabPermissions: PointerHandler.CanTakeOverFromHandlersOfDifferentType
                           | PointerHandler.ApprovesTakeOverByAnything
            onActiveChanged: if (active) root.startSystemMove()
        }

        // Кнопки в правом верхнем углу
        Row {
            anchors { top: parent.top; right: parent.right; topMargin: 4; rightMargin: 4 }
            spacing: 2

            // Свернуть в трей
            Rectangle {
                width: 28; height: 24; radius: 4
                color: minHover.containsMouse ? backend.colors.bg_btn_sec : "transparent"
                MouseArea {
                    id: minHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.minimizeToTray()
                }
                Text {
                    anchors { centerIn: parent; verticalCenterOffset: -2 }
                    text: "–"
                    color: minHover.containsMouse ? backend.colors.text_primary : backend.colors.text_muted
                    font { pixelSize: 18; family: "Segoe UI" }
                }
            }

            // Закрыть
            Rectangle {
                width: 28; height: 24; radius: 4
                color: closeHover.containsMouse ? backend.colors.close_hover : "transparent"
                MouseArea {
                    id: closeHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.requestClose()
                }
                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: closeHover.containsMouse ? "#ffffff" : backend.colors.text_muted
                    font { pixelSize: 15; family: "Segoe UI" }
                }
            }
        }

        ColumnLayout {
            id: mainCol
            anchors { left: parent.left; right: parent.right; top: parent.top }
            anchors.margins: 24
            spacing: 0

            // ── Заголовок ─────────────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 22
                spacing: 6

                Text {
                    text: backend.strings.title
                    color: backend.colors.text_primary
                    font { pixelSize: 16; weight: Font.Bold; family: "Segoe UI" }
                }
                Item { Layout.fillWidth: true }

                // Переключатель темы
                Rectangle {
                    width: 34; height: 24; radius: 4
                    color: themeHover.containsMouse ? backend.colors.bg_btn_sec_hov
                                                   : backend.colors.bg_btn_sec
                    MouseArea {
                        id: themeHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !backend.downloading
                        onClicked: backend.toggleTheme()
                    }
                    Text {
                        anchors.centerIn: parent
                        text: backend.theme === "dark" ? "☀" : "☾"
                        color: themeHover.containsMouse ? backend.colors.text_primary
                                                       : backend.colors.text_secondary
                        font { pixelSize: 14; family: "Segoe UI" }
                    }
                }

                // Переключатель языка
                Rectangle {
                    width: 34; height: 24; radius: 4
                    color: langHover.containsMouse ? backend.colors.bg_btn_sec_hov
                                                  : backend.colors.bg_btn_sec
                    MouseArea {
                        id: langHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !backend.downloading
                        onClicked: backend.toggleLanguage()
                    }
                    Text {
                        anchors.centerIn: parent
                        text: backend.lang === "en" ? "RU" : "EN"
                        color: langHover.containsMouse ? backend.colors.text_primary
                                                      : backend.colors.text_secondary
                        font { pixelSize: 11; weight: Font.Bold; family: "Segoe UI" }
                    }
                }
            }

            // ── Разделитель ───────────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: backend.colors.separator
                Layout.topMargin: 12
                Layout.bottomMargin: 18
            }

            // ── ID канала ─────────────────────────────────────────────────────
            Text {
                text: backend.strings.channel_label
                color: backend.colors.text_label
                font { pixelSize: 10; weight: Font.Bold; family: "Segoe UI"; letterSpacing: 0.5 }
            }
            Item { height: 5 }
            TextField {
                id: channelField
                Layout.fillWidth: true
                placeholderText: backend.strings.channel_hint
                enabled: !backend.downloading
                color: backend.colors.text_input
                placeholderTextColor: backend.colors.text_placeholder
                selectionColor: backend.colors.accent
                font { pixelSize: 13; family: "Segoe UI" }
                leftPadding: 10; rightPadding: 10; topPadding: 8; bottomPadding: 8
                background: Rectangle {
                    color: channelField.enabled ? backend.colors.bg_input
                                               : backend.colors.bg_input_dis
                    radius: 4
                    border.width: 1.5
                    border.color: channelField.activeFocus ? backend.colors.accent
                                                          : backend.colors.border_input
                }
            }
            Item { height: 14 }

            // ── Токен ─────────────────────────────────────────────────────────
            Text {
                text: backend.strings.token_label
                color: backend.colors.text_label
                font { pixelSize: 10; weight: Font.Bold; family: "Segoe UI"; letterSpacing: 0.5 }
            }
            Item { height: 5 }
            TextField {
                id: tokenField
                Layout.fillWidth: true
                placeholderText: backend.strings.token_hint
                echoMode: TextInput.Password
                enabled: !backend.downloading
                color: backend.colors.text_input
                placeholderTextColor: backend.colors.text_placeholder
                selectionColor: backend.colors.accent
                font { pixelSize: 13; family: "Segoe UI" }
                leftPadding: 10; rightPadding: 10; topPadding: 8; bottomPadding: 8
                background: Rectangle {
                    color: tokenField.enabled ? backend.colors.bg_input
                                             : backend.colors.bg_input_dis
                    radius: 4
                    border.width: 1.5
                    border.color: tokenField.activeFocus ? backend.colors.accent
                                                        : backend.colors.border_input
                }
            }
            Item { height: 14 }

            // ── Выбор папки ───────────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    height: 36
                    implicitWidth: folderBtnText.implicitWidth + 28
                    radius: 4
                    color: folderHover.pressed       ? backend.colors.bg_btn_sec_press
                         : folderHover.containsMouse ? backend.colors.bg_btn_sec_hov
                         : backend.colors.bg_btn_sec
                    MouseArea {
                        id: folderHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !backend.downloading
                        onClicked: backend.chooseFolder()
                    }
                    Text {
                        id: folderBtnText
                        anchors.centerIn: parent
                        text: backend.strings.choose_folder
                        color: backend.colors.text_btn_sec
                        font { pixelSize: 12; family: "Segoe UI" }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: backend.folderDisplay
                    color: backend.colors.text_muted
                    font { pixelSize: 11; family: "Segoe UI" }
                    elide: Text.ElideMiddle
                }
            }
            Item { height: 16 }

            // ── Кнопка скачивания ─────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                height: 42
                radius: 4
                color: {
                    const active = tokenField.text && channelField.text && !backend.downloading
                    if (!active)              return backend.colors.bg_btn_sec
                    if (dlHover.pressed)      return backend.colors.accent_pressed
                    if (dlHover.containsMouse) return backend.colors.accent_hover
                    return backend.colors.accent
                }
                MouseArea {
                    id: dlHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    enabled: tokenField.text && channelField.text && !backend.downloading
                    onClicked: backend.startDownload(tokenField.text, channelField.text)
                }
                Text {
                    anchors.centerIn: parent
                    text: backend.strings.download_btn
                    color: (tokenField.text && channelField.text && !backend.downloading)
                           ? "#ffffff" : backend.colors.text_muted
                    font { pixelSize: 14; weight: Font.DemiBold; family: "Segoe UI" }
                }
            }

            // ── Прогресс (только во время загрузки) ──────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                Layout.topMargin: 16
                spacing: 6
                visible: backend.downloading

                ProgressBar {
                    id: progressBar
                    Layout.fillWidth: true
                    value: backend.total > 0 ? backend.progress / backend.total : 0
                    indeterminate: backend.total === 0
                    contentItem: Item {
                        id: progressContent
                        clip: true
                        Rectangle {
                            id: progressFill
                            width: progressBar.indeterminate
                                   ? progressContent.width * 0.3
                                   : progressContent.width * progressBar.value
                            height: progressContent.height
                            radius: 7
                            color: backend.colors.accent

                            NumberAnimation on x {
                                running: progressBar.indeterminate
                                from: -progressFill.width
                                to: progressContent.width
                                duration: 1200
                                loops: Animation.Infinite
                            }
                        }
                    }
                    background: Rectangle {
                        color: backend.colors.bg_input
                        radius: 7
                        implicitHeight: 14
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignRight
                    text: backend.progressText
                    color: backend.colors.text_muted
                    font { pixelSize: 11; family: "Segoe UI" }
                }
            }

            Item { height: 22 }
        }
    }
}
