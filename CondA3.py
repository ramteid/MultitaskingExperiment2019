# coding=utf-8
#############################
#  Multitasking experiment: Typing digits (keyboard) while tracking (joystick)
#  Developed by Dietmar Sach (dsach@mail.de) for the Institute of Sport Science of the University of Augsburg
#  Based on a script made by Christian P. Janssen, c.janssen@ucl.ac.uk December 2009 - March 2010
#############################
import csv
import datetime
import inspect
import math
import os
import random
import time
import traceback
from enum import Enum
from os import path
from tkinter import *
import pygame
import scipy
import scipy.special


class Vector2D:
    """
    Used to represent coordinates or measures with x and y.
    Do not modify anything here!
    """
    X = 0
    Y = 0

    def __init__(self, x, y):
        self.X = x
        self.Y = y


class ExperimentSettings:
    """
    These settings can be modified by the Experiment supervisor
    """
    CircleBorderThickness = 5
    SingleTypingTaskNumbers = "123"
    SingleTypingTaskNumbersLength = 27

    MaxTrialTimeDual = 90  # maximum time for dual-task trials
    MaxTrialTimeSingleTracking = 10  # maximum time for single-task tracking
    MaxTrialTimeSingleTyping = 20  # maximum time for single-task typing

    TaskWindowSize = Vector2D(550, 550)
    SpaceBetweenWindows = 128

    # Settings used for displaying Typing Task within Cursor
    GeneralFontSize = 30
    FontSizeTypingTaskNumberSingleTask = 30
    FontSizeTypingTaskNumberWithinCursor = 30
    FontColorTypingTaskNumberWithinCursor = (255, 255, 255)
    CursorSize = Vector2D(20, 20)
    CursorColorInside = (255, 0, 0)  # red
    CursorColorOutside = (0, 0, 255)  # blue

    # General settings
    CursorNoises = {"high": 5, "medium": 4, "low": 3}  # This is the speed of the cursor movement (standard deviation of noise)
    TimeFeedbackIsDisplayed = 4
    BackgroundColorTaskWindows = (255, 255, 255)  # white
    BackgroundColorEntireScreen = (50, 50, 50)  # gray
    CoverColor = (200, 200, 200)  # very light gray

    # Practice trials settings
    CursorNoisePracticeTrials = CursorNoises["high"]

    # Debug mode will speed up the messages and the trials for debugging. Should be set to False for normal use.
    DebugMode = False


class Constants:
    Title = "Multitasking 3.0"
    ExperimentWindowSize = Vector2D(1280, 1024)
    MotionTolerance = 0.08
    OffsetTop = 50
    OffsetTaskWindowsTop = 50  # is overwritten for parallel dual task mode
    OffsetLeftRight = int((ExperimentWindowSize.X - ExperimentSettings.SpaceBetweenWindows - 2 * ExperimentSettings.TaskWindowSize.X) / 2)
    TopLeftCornerOfTypingTaskWindow = Vector2D(OffsetLeftRight, OffsetTaskWindowsTop)
    TopLeftCornerOfTrackingTaskWindow = Vector2D(OffsetLeftRight + ExperimentSettings.TaskWindowSize.X + ExperimentSettings.SpaceBetweenWindows, OffsetTaskWindowsTop)
    TrackingWindowMiddleX = TopLeftCornerOfTrackingTaskWindow.X + int(ExperimentSettings.TaskWindowSize.X / 2.0)
    TrackingWindowMiddleY = TopLeftCornerOfTrackingTaskWindow.Y + int(ExperimentSettings.TaskWindowSize.Y / 2.0)
    ScalingJoystickAxis = 5  # how many pixels the cursor moves when joystick is at full angle (value of 1 or -1).
    StepSizeOfTrackingScreenUpdate = 0.005  # how many seconds does it take for a screen update
    SettingsFilename = "guiconfig.dat"


class RuntimeVariables:
    """
    These variables are managed by the program itself.
    Do not modify anything here!
    """
    BlockNumber = 0
    CirclesSmall = []
    CirclesBig = []
    CirclesPractice = []
    CumulatedTrackingScoreForParallelDualTasks = 0
    CurrentCircles = []  # is set for each condition
    CurrentTypingTaskNumbers = ""
    CurrentTypingTaskNumbersLength = 1
    CurrentTaskType = None
    CurrentCursorColor = ExperimentSettings.CursorColorInside
    CombinedFeedback = False
    CorrectlyTypedDigitsVisit = 0
    CurrentCondition = ""
    CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)
    CursorDistancesToMiddle = []
    DictTrialListEntries = {}
    DigitPressTimes = []
    DisableCorrectTypingScoreOutsideCircle = False
    DisplayScoreForNormalTrials = False
    DisplayScoreForPracticeTrials = False
    DisplayTypingTaskWithinCursor = False
    EnteredDigitsStr = ""
    EnvironmentIsRunning = False
    FeedbackMode = None
    IncorrectlyTypedDigitsTrial = 0
    IncorrectlyTypedDigitsVisit = 0
    JoystickAxis = Vector2D(0, 0)  # the motion of the joystick
    JoystickObject = None
    LengthOfPathTracked = 0
    NumberOfCircleExits = 0
    OutputDataFile = None
    OutputDataFileTrialEnd = None
    ParallelDualTasks = False
    Penalty = None
    PenaltyPracticeTrials = None
    PenaltyAmount = 0
    RunningOrder = []
    RunPracticeTrials = True
    ShowOnlyGetReadyMessage = False
    ShowPenaltyRewardNoise = True
    IntervalForFeedbackAfterTrials = None
    DualTaskScoreOverAllConditions = []
    Screen = None
    StandardDeviationOfNoise = None
    StartTimeCurrentTrial = time.time()
    StartTimeOfFirstExperiment = time.time()
    ParticipantNumber = "0"
    TrackingTaskPresent = False
    TrackingWindowEntryCounter = 0
    TrackingWindowVisible = False
    TrialNumber = 0
    TrialScore = 0
    TypingPenaltyIncorrectDigit = 5
    TypingRewardCorrectDigit = 0
    TypingTaskPresent = False
    TypingWindowEntryCounter = 0
    TypingWindowVisible = False
    VisitEndTime = 0
    VisitScore = 0
    VisitStartTime = 0
    WasCursorOutsideRadiusBefore = False


class TaskTypes(Enum):
    """
    Used to represent different task types.
    Do not modify anything here!
    """
    SingleTracking = 1
    SingleTyping = 2
    DualTask = 3
    PracticeSingleTracking = 4
    PracticeSingleTyping = 5
    PracticeDualTask = 6


class Penalty(Enum):
    """
    Used to represent different penalties.
    Do not modify anything here!
    """
    NoPenalty = 1  # Do not change the score
    LoseAll = 2
    LoseHalf = 3
    LoseAmount = 4  # Lose an amount specified in RuntimeVariables.PenaltyAmount


class Block:
    """
    Used to represent a block of trials.
    Do not modify anything here!
    """
    TaskType = None
    NumberOfTrials = 0

    def __init__(self, taskType, numberOfTrials):
        self.TaskType = taskType
        self.NumberOfTrials = numberOfTrials


class Circle:
    """
    Used to represent a circle.
    Do not modify anything here!
    """
    Radius = 0
    TypingTaskNumbersDualTask = ""
    InnerCircleColor = (255, 204, 102)  # orange
    BorderColor = (255, 0, 0)  # red

    def __init__(self, radius, typingTaskNumbersDualTask, innerCircleColor, borderColor):
        self.Radius = radius
        self.TypingTaskNumbersDualTask = typingTaskNumbersDualTask
        self.InnerCircleColor = innerCircleColor
        self.BorderColor = borderColor


def CalculateFeedbackParallelDualTasks():
    factorTyping = 1.0
    typingScore = factorTyping * RuntimeVariables.CorrectlyTypedDigitsVisit  # One Visit equals one Trial in parallel dual tasks
    typingScore = int(typingScore)  # cut all decimal places

    factorTracking = 1.0
    trackingScore = calculateRmse()
    if trackingScore > 0:  # avoid division by zero!
        trackingScore = factorTracking * (1.0 / trackingScore)  # Invert RMSE as a higher score should be better.

    # For live feedback, the tracking score must increase over time. To be compareable, it should be calculated the same way for non-live feedback.
    RuntimeVariables.CumulatedTrackingScoreForParallelDualTasks += trackingScore
    cumulatedTrackingScore = int(RuntimeVariables.CumulatedTrackingScoreForParallelDualTasks)

    combinedScore = (typingScore + RuntimeVariables.CumulatedTrackingScoreForParallelDualTasks) / 2.0
    combinedScore = int(combinedScore)  # cut all decimal places

    return typingScore, cumulatedTrackingScore, combinedScore  # return a three-tuple with all feedback


def DisplayLiveFeedbackParallelDualTasks(taskType: TaskTypes):
    if not RuntimeVariables.ParallelDualTasks:
        raise Exception("Should not display scores for parallel dual task experiments in switching dual task setup")
    scores = CalculateFeedbackParallelDualTasks()
    typingScore = scores[0]
    trackingScore = scores[1]
    combinedScore = scores[2]
    boxWidth = 200
    boxHeight = 50
    offsetLeft = 0
    text = ""
    if taskType == TaskTypes.SingleTyping:
        text = f"Punkte: {typingScore}"
        offsetLeft = ((Constants.TopLeftCornerOfTypingTaskWindow.X + ExperimentSettings.TaskWindowSize.X) / 2) - (boxWidth / 2)
    elif taskType == TaskTypes.SingleTracking:
        text = f"Punkte: {trackingScore}"
        offsetLeft = ((Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X) / 2) - (boxWidth / 2)
    elif taskType == TaskTypes.DualTask and RuntimeVariables.CombinedFeedback:
        offsetLeft = (Constants.ExperimentWindowSize.X / 2) - (boxWidth / 2)
        text = f"Punkte: {combinedScore}"
    elif taskType == TaskTypes.DualTask and not RuntimeVariables.CombinedFeedback and RuntimeVariables.DisplayTypingTaskWithinCursor:
        offsetLeft = (Constants.ExperimentWindowSize.X / 2) - (boxWidth / 2)
        boxWidth += 100
        boxHeight += 10
        text = f"Punkte Tippen: {typingScore}\nPunkte Tracking: {trackingScore}"
    elif taskType == TaskTypes.DualTask and not RuntimeVariables.CombinedFeedback:
        boxWidth += 100
        text = [f"Punkte Tippen: {typingScore}", f"Punkte Tracking: {trackingScore}"]

    top = Constants.OffsetTaskWindowsTop - boxHeight - 10
    if not taskType == TaskTypes.DualTask or RuntimeVariables.CombinedFeedback or RuntimeVariables.DisplayTypingTaskWithinCursor:
        bg = pygame.Surface((boxWidth, boxHeight)).convert()
        bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
        RuntimeVariables.Screen.blit(bg, (offsetLeft, top))
        printTextOverMultipleLines(text, Vector2D(offsetLeft + 10, top + 10))
    elif taskType == TaskTypes.DualTask and not RuntimeVariables.CombinedFeedback:
        # draw typing feedback box
        offsetLeft = ((Constants.TopLeftCornerOfTypingTaskWindow.X + ExperimentSettings.TaskWindowSize.X) / 2) - (boxWidth / 2)
        bg = pygame.Surface((boxWidth, boxHeight)).convert()
        bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
        RuntimeVariables.Screen.blit(bg, (offsetLeft, top))
        printTextOverMultipleLines(text[0], Vector2D(offsetLeft + 10, top + 10))
        # draw tracking feedback box
        offsetLeft = Constants.TopLeftCornerOfTrackingTaskWindow.X + (ExperimentSettings.TaskWindowSize.X / 2) - (boxWidth / 2)
        bg = pygame.Surface((boxWidth, boxHeight)).convert()
        bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
        RuntimeVariables.Screen.blit(bg, (offsetLeft, top))
        printTextOverMultipleLines(text[1], Vector2D(offsetLeft + 10, top + 10))
    else:
        raise Exception("Unknown parallel dual task live feedback mode")


def DisplayFeedbackParallelDualTasksAfterTrial():
    """
    When parallel dual tasks are activated:
    Displays feedback for dual tasks, and single tasks at the end of a trial
    """
    if not RuntimeVariables.ParallelDualTasks:
        raise Exception("Should not display scores for parallel dual task experiments in switching dual task setup")
    scores = CalculateFeedbackParallelDualTasks()
    typingScore = scores[0]
    trackingScore = scores[1]
    combinedScore = scores[2]
    message = ""
    scoreForLogging = ""
    # For combined feedback ...
    if RuntimeVariables.CurrentTaskType == TaskTypes.DualTask:
        RuntimeVariables.DualTaskScoreOverAllConditions.append(combinedScore)  # store dual task score, it will be displayed at the end of each block
        if RuntimeVariables.CombinedFeedback:
            message = f"Punktestand: {combinedScore}"
            scoreForLogging = str(combinedScore)
        # For separate feedback ...
        else:
            message = f"Punktestand:\n\nTippen: {typingScore}          Tracking: {trackingScore}"
            scoreForLogging = f"{typingScore}, {trackingScore}"
    elif RuntimeVariables.CurrentTaskType == TaskTypes.SingleTyping:
        message = f"Punktestand:\n\nTippen: {typingScore}"
        scoreForLogging = f"{typingScore}"
    elif RuntimeVariables.CurrentTaskType == TaskTypes.SingleTracking:
        message = f"Punktestand:\n\nTracking: {trackingScore}"
        scoreForLogging = f"{trackingScore}"
    DisplayMessage(message, ExperimentSettings.TimeFeedbackIsDisplayed)
    writeOutputDataFile("scoreDisplayed", scoreForLogging)


def DisplayFeedbackSwitchingDualTaskAfterTrial():
    """Displays feedback message after trial. Only used for switching dual task."""
    if RuntimeVariables.ParallelDualTasks:
        raise Exception("Should not display scores for switching dual task experiments in parallel dual task setup")
    scoreForLogging = "-"  # score that's logged

    if RuntimeVariables.CurrentTaskType == TaskTypes.DualTask:
        feedbackScore = RuntimeVariables.TrialScore
        if RuntimeVariables.TrialScore > 0:
            feedbackText = "+" + str(feedbackScore) + " Punkte"
        else:
            feedbackText = str(feedbackScore) + " Punkte"

        RuntimeVariables.DualTaskScoreOverAllConditions.append(RuntimeVariables.TrialScore)  # store dual task score, it will be displayed at the end of each block
        scoreForLogging = RuntimeVariables.TrialScore
        DisplayMessage(feedbackText, ExperimentSettings.TimeFeedbackIsDisplayed)

    elif RuntimeVariables.CurrentTaskType == TaskTypes.SingleTyping:
        feedbackText = "Anzahl Fehler: \n"
        digitScore = RuntimeVariables.DigitPressTimes[-1] - RuntimeVariables.DigitPressTimes[0]
        digitScore = scipy.special.round(digitScore * 10) / 10  # round values
        feedbackText += "\n\n" + str(RuntimeVariables.IncorrectlyTypedDigitsTrial) + " Fehler"
        scoreForLogging = digitScore
        DisplayMessage(feedbackText, ExperimentSettings.TimeFeedbackIsDisplayed)

    writeOutputDataFile("scoreDisplayed", str(scoreForLogging))


def calculateRmse():
    """
    The RMSE is calculated from all collected distances in this trial.
    The distances are collected each time the cursor changes its position.
    The RMSE is calculated every time the data file is written.
    """
    n = len(RuntimeVariables.CursorDistancesToMiddle)
    if n == 0:
        return 0
    square = 0

    # Calculate square
    for val in RuntimeVariables.CursorDistancesToMiddle:
        square += val * val

    # Calculate Mean
    mean = (square / float(n))
    # Calculate Root
    root = math.sqrt(mean)
    return root


def checkMouseClicked():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quitApp()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            posString = str(pos[0]) + "_" + str(pos[1])
            writeOutputDataFile("MousePressed", posString)
            return pos[0], pos[1]
    return False


def checkKeyPressed():
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and RuntimeVariables.TrackingWindowVisible:
            pos = pygame.mouse.get_pos()
            RuntimeVariables.CursorCoordinates = Vector2D(pos[0], pos[1])
        elif event.type == pygame.QUIT:
            quitApp()
        elif event.type == pygame.JOYAXISMOTION:
            if RuntimeVariables.TrackingTaskPresent:
                # values between -1 and 1. (-1,-1) top left corner, (1,-1) top right; (-1,1) bottom left, (1,1) bottom right
                try:
                    RuntimeVariables.JoystickAxis = Vector2D(RuntimeVariables.JoystickObject.get_axis(0), RuntimeVariables.JoystickObject.get_axis(1))
                except (pygame.error, NameError, AttributeError):
                    # prevent the program crashing when no joystick is connected
                    pass
        elif event.type == pygame.JOYBUTTONUP and not RuntimeVariables.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTyping")
                writeOutputDataFile("ButtonRelease", "-")
        elif event.type == pygame.JOYBUTTONDOWN and not RuntimeVariables.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")

        elif event.type == pygame.KEYDOWN:
            # F1 key switches windows, alternatively to the joystick button
            if event.key == pygame.K_F1 and RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TypingTaskPresent and not RuntimeVariables.ParallelDualTasks:
                switchWindows("openTyping")
                writeOutputDataFile("ButtonRelease", "-")
            elif event.key == pygame.K_F1 and RuntimeVariables.TypingWindowVisible and RuntimeVariables.TrackingTaskPresent and not RuntimeVariables.ParallelDualTasks:
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")
            # F4 key closes the program
            elif event.key == pygame.K_F4:
                quitApp("F4 was typed to terminate the app")
            else:
                # only process keypresses if the digit task is present
                singleTypingTask = RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible
                dualTaskWithSwitching = RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible
                dualTaskParallel = RuntimeVariables.TypingTaskPresent and not RuntimeVariables.TypingWindowVisible and RuntimeVariables.ParallelDualTasks
                if singleTypingTask or dualTaskWithSwitching or dualTaskParallel:
                    key = event.unicode
                    RuntimeVariables.DigitPressTimes.append(time.time())

                    isCorrectKeyPress = key == RuntimeVariables.CurrentTypingTaskNumbers[0]

                    isNeutralKeyPress = False
                    # In parallel dual task, e is to be typed when the cursor was outside the circle. On e, all key presses are neither correct or incorrect.
                    if RuntimeVariables.CurrentTypingTaskNumbers[0] == "e" and RuntimeVariables.ParallelDualTasks and (RuntimeVariables.CurrentTaskType == TaskTypes.DualTask or RuntimeVariables.CurrentTaskType == TaskTypes.PracticeDualTask):
                        isNeutralKeyPress = True
                    # In non-parallel dual tasks, if the cursor is outside the circle and correct inputs don't count outside, treat correct inputs as neutral.
                    if not RuntimeVariables.ParallelDualTasks and RuntimeVariables.DisableCorrectTypingScoreOutsideCircle and isCursorOutsideCircle() and isCorrectKeyPress:
                        isNeutralKeyPress = True

                    # Neutral key presses don't count as correct nor incorrect.
                    if isNeutralKeyPress:
                        RuntimeVariables.EnteredDigitsStr += key
                        UpdateTypingTaskString(reset=False)  # generate one new character
                        writeOutputDataFile("keypress", key)
                        print(f"Neutral key press: {key}")
                    # If key press is correct ...
                    elif isCorrectKeyPress:
                        RuntimeVariables.EnteredDigitsStr += key
                        UpdateTypingTaskString(reset=False)  # generate one new character
                        RuntimeVariables.CorrectlyTypedDigitsVisit += 1
                        writeOutputDataFile("keypress", key)
                        print(f"Correct key press: {key}")
                    # If key press is wrong ...
                    else:
                        RuntimeVariables.IncorrectlyTypedDigitsTrial += 1
                        RuntimeVariables.IncorrectlyTypedDigitsVisit += 1
                        writeOutputDataFile("wrongKeypress", key)
                        print(f"Incorrect key press: {key}")

                    if RuntimeVariables.CurrentTaskType in [TaskTypes.SingleTyping, TaskTypes.PracticeSingleTyping] or not RuntimeVariables.DisplayTypingTaskWithinCursor:
                        drawTypingWindow()


def switchWindows(taskToOpen):
    # switching is only done in dual-task
    if RuntimeVariables.CurrentTaskType == TaskTypes.DualTask or RuntimeVariables.CurrentTaskType == TaskTypes.PracticeDualTask:
        if taskToOpen == "openTracking":
            if not RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TrackingTaskPresent:
                openTrackingWindow()
            if RuntimeVariables.TypingWindowVisible and RuntimeVariables.TypingTaskPresent:
                closeTypingWindow()
        elif taskToOpen == "openTyping":
            if not RuntimeVariables.TypingWindowVisible and RuntimeVariables.TypingTaskPresent:
                openTypingWindow()
            if RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TrackingTaskPresent:
                closeTrackingWindow()


def printTextOverMultipleLines(text, location: Vector2D):
    fontsize = ExperimentSettings.GeneralFontSize
    color = (0, 0, 0)
    pygame.event.pump()
    splittedText = text.split("\n")
    lineDistance = (pygame.font.Font(None, fontsize)).get_linesize()
    PositionX = location.X
    PositionY = location.Y

    for lines in splittedText:
        f = pygame.font.Font(None, fontsize)
        msg = f.render(lines, True, color)
        RuntimeVariables.Screen.blit(msg, (PositionX, PositionY))
        PositionY = PositionY + lineDistance


def CountdownMessage(displayTime):
    if ExperimentSettings.DebugMode:  # change some settings to facilitate debugging
        displayTime = 1
    for i in range(0, displayTime):
        # prepare background
        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))

        messageAreaObject = pygame.Surface((int(Constants.ExperimentWindowSize.X / 5), int(Constants.ExperimentWindowSize.Y / 5))).convert()
        messageAreaObject.fill((255, 255, 255))

        topCornerOfMessageArea = Vector2D(int(Constants.ExperimentWindowSize.X * 2 / 5), int(Constants.TopLeftCornerOfTypingTaskWindow.Y + 10))
        RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))

        message = "Mach dich bereit!\n\n" \
                  "            " + str(displayTime - i)

        pygame.display.flip()
        printTextOverMultipleLines(message, Vector2D(topCornerOfMessageArea.X + 45, topCornerOfMessageArea.Y + 10))
        writeLogFile(message)
        pygame.display.flip()
        time.sleep(1)


def DisplayMessage(message, displayTime):
    if ExperimentSettings.DebugMode:  # change some settings to facilitate debugging
        displayTime = 1
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))
    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))
    topCornerOfMessageArea = Vector2D(Constants.OffsetLeftRight, Constants.OffsetTop)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))
    location = Vector2D(topCornerOfMessageArea.X + Constants.OffsetLeftRight + 25, topCornerOfMessageArea.Y + Constants.OffsetTop + 25)
    printTextOverMultipleLines(message, Vector2D(location.X, location.Y))
    pygame.display.flip()
    writeLogFile(message)
    time.sleep(displayTime)


def drawCanvas():
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))
    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))
    topCornerOfMessageArea = Vector2D(Constants.OffsetLeftRight, Constants.OffsetTop)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))
    buttonAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 300, Constants.ExperimentWindowSize.Y - 300)).convert()
    buttonAreaObject.fill((150, 150, 150))
    RuntimeVariables.Screen.blit(buttonAreaObject, (150, 150))


def UpdateTypingTaskString(reset=False):
    """
    Updates the typing task number string.
    :param reset: Set to True if you want to generate a completely new string
    """
    if reset:
        RuntimeVariables.CurrentTypingTaskNumbers = ""
    # Remove the leftmost character
    RuntimeVariables.CurrentTypingTaskNumbers = RuntimeVariables.CurrentTypingTaskNumbers[1:]
    # Generate random characters until the string is complete
    numberOfNewCharacters = RuntimeVariables.CurrentTypingTaskNumbersLength - len(RuntimeVariables.CurrentTypingTaskNumbers)
    if numberOfNewCharacters > 0:
        newCharacters = GetTypingTaskNumbers(numberOfNewCharacters)
        # Update the typing task string. Append the new numbers on the right hand side.
        RuntimeVariables.CurrentTypingTaskNumbers += newCharacters


def GetTypingTaskNumbers(count):
    """
    Returns a random string of characters that are used in the typing task string, depending on the cursor position.
    Returns e if the cursor is outside of the circle.
    :param count: Specifies how many numbers you want
    :return: A string with <count> numbers
    """

    # For single typing task or regular dual task with switching, return the single task string
    isSwitchingDualTask = RuntimeVariables.CurrentTaskType in [TaskTypes.DualTask, TaskTypes.PracticeDualTask] and not RuntimeVariables.ParallelDualTasks
    isSingleTypingTask = RuntimeVariables.CurrentTaskType in [TaskTypes.SingleTyping, TaskTypes.PracticeSingleTyping]
    if isSwitchingDualTask or isSingleTypingTask:
        return ''.join([random.choice(ExperimentSettings.SingleTypingTaskNumbers) for _ in range(count)])

    # For dual task with both tracking and typing window visible, determine the typing string from the cursor position
    distanceCursorMiddle = math.sqrt((abs(Constants.TrackingWindowMiddleX - RuntimeVariables.CursorCoordinates.X)) ** 2 + (abs(Constants.TrackingWindowMiddleY - RuntimeVariables.CursorCoordinates.Y)) ** 2)
    possibleCharacters = None
    for circle in RuntimeVariables.CurrentCircles:
        if distanceCursorMiddle < circle.Radius:
            possibleCharacters = circle.TypingTaskNumbersDualTask
            break

    # If the cursor is outside the outermost circle radius, the tpying task should show an "e"
    if not possibleCharacters and RuntimeVariables.ParallelDualTasks and RuntimeVariables.CurrentTaskType in [TaskTypes.DualTask, TaskTypes.PracticeDualTask]:
        possibleCharacters = "e"
    elif not possibleCharacters:
        raise Exception("Could not get a random typing task number for the current circle radius!")

    # Return the specified number of random characters
    return ''.join([random.choice(possibleCharacters) for _ in range(count)])


def drawCircles(bg):
    for circle in reversed(RuntimeVariables.CurrentCircles):
        # draw a filled circle
        drawCircle(bg, circle.InnerCircleColor, circle.Radius, 0)
        # Draws a circular shape on the Surface. The pos argument is the center of the circle, and radius is the size.
        #  The width argument is the thickness to draw the outer edge. If width is zero then the circle will be filled.
        drawCircle(bg, circle.BorderColor, circle.Radius, ExperimentSettings.CircleBorderThickness)


def drawCircle(image, colour, radius, width=0):
    origin = Vector2D(int(ExperimentSettings.TaskWindowSize.X / 2), int(ExperimentSettings.TaskWindowSize.Y / 2))
    # based on recommendation on pygame website
    if width == 0:
        pygame.draw.circle(image, colour, (origin.X, origin.Y), int(radius))
    else:
        if radius > 65534 / 5:
            radius = 65534 / 5
        circle = pygame.Surface([radius * 2 + width, radius * 2 + width]).convert_alpha()
        circle.fill([0, 0, 0, 0])
        pygame.draw.circle(circle, colour, (int(circle.get_width() / 2), int(circle.get_height() / 2)), int(radius + (width / 2)))
        if int(radius - (width / 2)) > 0:
            pygame.draw.circle(circle, [0, 0, 0, 0], (int(circle.get_width() / 2), int(circle.get_height() / 2)), abs(int(radius - (width / 2))))
        image.blit(circle, [origin.X - (circle.get_width() / 2), origin.Y - (circle.get_height() / 2)])


def updateCursor(sleepTime):
    x = RuntimeVariables.CursorCoordinates.X
    y = RuntimeVariables.CursorCoordinates.Y
    oldX = RuntimeVariables.CursorCoordinates.X
    oldY = RuntimeVariables.CursorCoordinates.Y

    # only add noise if tracking is not moving.
    # define joystick as moved if one of its axis is in [-1, -0.08] or [0.08, 1]. Joystick precision requires this.
    joystickIsMoving = RuntimeVariables.JoystickAxis.X > Constants.MotionTolerance or \
                       RuntimeVariables.JoystickAxis.X < -Constants.MotionTolerance or \
                       RuntimeVariables.JoystickAxis.Y > Constants.MotionTolerance or \
                       RuntimeVariables.JoystickAxis.Y < -Constants.MotionTolerance

    # Always add random noise, except when the tracking window is visible and the joystick is moved
    if not (RuntimeVariables.TrackingWindowVisible and joystickIsMoving):
        final_x = x + random.gauss(0, RuntimeVariables.StandardDeviationOfNoise)
        final_y = y + random.gauss(0, RuntimeVariables.StandardDeviationOfNoise)
    else:
        final_x = x
        final_y = y

    # Apply the joystick movement to the cursor, but only if the tracking window is open (i.e. when the participant sees what way the cursor moves!)
    if RuntimeVariables.TrackingWindowVisible:
        final_x += RuntimeVariables.JoystickAxis.X * Constants.ScalingJoystickAxis
        final_y += RuntimeVariables.JoystickAxis.Y * Constants.ScalingJoystickAxis

    # now iterate through updates (but only do that if the window is open - if it's closed do it without mini-steps, so as to make computation faster)
    nrUpdates = int(sleepTime / Constants.StepSizeOfTrackingScreenUpdate)
    delta_x = (final_x - x) / nrUpdates
    delta_y = (final_y - y) / nrUpdates

    if RuntimeVariables.TrackingWindowVisible:
        drawTrackingWindow()
        drawCursor()

        for i in range(0, nrUpdates):
            x += delta_x
            y += delta_y

            if x != RuntimeVariables.CursorCoordinates.X and y != RuntimeVariables.CursorCoordinates.Y:
                # now check if the cursor is still within screen range
                if x < (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2):
                    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2
                elif x > (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2):
                    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2

                if y < (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2):
                    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2
                elif y > (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2):
                    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2

                drawCursor()
                if RuntimeVariables.CurrentTaskType in [TaskTypes.DualTask, TaskTypes.PracticeDualTask] and RuntimeVariables.DisplayTypingTaskWithinCursor and RuntimeVariables.ParallelDualTasks:
                    drawTypingTaskWithinCursor()

            pygame.display.flip()
            time.sleep(Constants.StepSizeOfTrackingScreenUpdate)

        # see if there is additional time to sleep
        mods = sleepTime % Constants.StepSizeOfTrackingScreenUpdate
        if mods != 0:
            time.sleep(mods)

    # if tracking window is not visible, just update the values
    else:
        # Apply random noise and joystick movement if present
        x = final_x
        y = final_y

        # now check if the cursor is still within screen range
        if x != RuntimeVariables.CursorCoordinates.X and y != RuntimeVariables.CursorCoordinates.Y:
            limitLeftX = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2
            limitLeftY = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2
            limitRightX = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2
            limitRightY = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2
            if x < limitLeftX:
                x = limitLeftX
            elif x > limitRightX:
                x = limitRightX
            if y < limitLeftY:
                y = limitLeftX
            elif y > limitRightY:
                y = limitRightY

        # if display is not updated, sleep for entire time
        time.sleep(sleepTime)

    # always update coordinates
    RuntimeVariables.CursorCoordinates = Vector2D(x, y)

    # collect distances of the cursor to the circle middle for the RMSE
    RuntimeVariables.CursorDistancesToMiddle.append(math.sqrt((Constants.TrackingWindowMiddleX - x) ** 2 + (Constants.TrackingWindowMiddleY - y) ** 2))

    # collect cumulatively the distance the cursor has moved
    RuntimeVariables.LengthOfPathTracked += math.sqrt((oldX - x) ** 2 + (oldY - y) ** 2)

    # Detect whether the cursor is outside the circle, also if tracking is not visible.
    isCursorOutsideCircleVar = isCursorOutsideCircle()
    if isCursorOutsideCircleVar:
        RuntimeVariables.CurrentCursorColor = ExperimentSettings.CursorColorInside
    else:
        RuntimeVariables.CurrentCursorColor = ExperimentSettings.CursorColorOutside

    # For Parallel DualTasks, update the typing task string on cursor leaving/reentering the circle
    if RuntimeVariables.TrackingWindowVisible:
        # When the cursor moves outside the circles, the parallel dual task typing number shall become "e" immediately
        if isCursorOutsideCircleVar and not RuntimeVariables.WasCursorOutsideRadiusBefore:
            RuntimeVariables.NumberOfCircleExits += 1
            if RuntimeVariables.ParallelDualTasks:
                RuntimeVariables.CurrentTypingTaskNumbers = "e"

        # When the cursor moves back inside the circles, the parallel dual task typing number shall become a number immediately
        if RuntimeVariables.ParallelDualTasks and not isCursorOutsideCircleVar and RuntimeVariables.WasCursorOutsideRadiusBefore and RuntimeVariables.CurrentTaskType not in [TaskTypes.SingleTracking, TaskTypes.PracticeSingleTracking]:
            UpdateTypingTaskString(reset=False)

    RuntimeVariables.WasCursorOutsideRadiusBefore = isCursorOutsideCircleVar


def isCursorOutsideCircle():
    try:
        position = RuntimeVariables.CursorCoordinates
        distanceCursorMiddle = math.sqrt((abs(Constants.TrackingWindowMiddleX - position.X)) ** 2 + (abs(Constants.TrackingWindowMiddleY - position.Y)) ** 2)
        largestCircleRadius = max(list(map(lambda circle: circle.Radius, RuntimeVariables.CurrentCircles)))
        return distanceCursorMiddle > largestCircleRadius
    except:
        return False


def drawTypingTaskWithinCursor():
    fontsize = ExperimentSettings.FontSizeTypingTaskNumberWithinCursor
    f = pygame.font.Font(None, fontsize)
    typingTaskNumberText = f.render(RuntimeVariables.CurrentTypingTaskNumbers, True, ExperimentSettings.FontColorTypingTaskNumberWithinCursor)
    textWidth, textHeight = f.size(RuntimeVariables.CurrentTypingTaskNumbers)
    x = RuntimeVariables.CursorCoordinates.X - (textWidth / 2)
    y = RuntimeVariables.CursorCoordinates.Y - (textHeight / 2)
    RuntimeVariables.Screen.blit(typingTaskNumberText, (x, y))


def closeTypingWindow():
    RuntimeVariables.TypingWindowVisible = False
    RuntimeVariables.VisitEndTime = time.time()


def drawCover(windowSide):
    if windowSide == "typing":
        location = Constants.TopLeftCornerOfTypingTaskWindow
    elif windowSide == "tracking":
        location = Constants.TopLeftCornerOfTrackingTaskWindow
    else:
        raise Exception("invalid window side specified")

    # draw background
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.CoverColor)
    RuntimeVariables.Screen.blit(bg, (location.X, location.Y))


def openTypingWindow():
    RuntimeVariables.VisitStartTime = time.time()
    RuntimeVariables.CorrectlyTypedDigitsVisit = 0
    RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
    RuntimeVariables.TypingWindowEntryCounter = RuntimeVariables.TypingWindowEntryCounter + 1
    drawTypingWindow()
    RuntimeVariables.TypingWindowVisible = True


def closeTrackingWindow():
    RuntimeVariables.TrackingWindowVisible = False
    RuntimeVariables.VisitEndTime = time.time()


def openTrackingWindow():
    RuntimeVariables.VisitStartTime = time.time()
    RuntimeVariables.TrackingWindowEntryCounter += 1
    RuntimeVariables.TrackingWindowVisible = True

    if RuntimeVariables.CurrentTaskType == TaskTypes.DualTask or RuntimeVariables.CurrentTaskType == TaskTypes.PracticeDualTask:
        ApplyRewardForTypingTaskScores()

    # get the cursor angle
    try:
        RuntimeVariables.JoystickAxis = Vector2D(RuntimeVariables.JoystickObject.get_axis(0), RuntimeVariables.JoystickObject.get_axis(1))
    except (pygame.error, NameError, AttributeError):
        # prevent the program crashing when no joystick is connected
        pass


def drawTypingWindow():
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
    RuntimeVariables.Screen.blit(bg, (Constants.TopLeftCornerOfTypingTaskWindow.X, Constants.TopLeftCornerOfTypingTaskWindow.Y))

    if not RuntimeVariables.ParallelDualTasks and (RuntimeVariables.CurrentTaskType == TaskTypes.DualTask or RuntimeVariables.CurrentTaskType == TaskTypes.PracticeDualTask):
        drawCover("tracking")

    f = pygame.font.Font(None, ExperimentSettings.FontSizeTypingTaskNumberSingleTask)
    typingTaskNumberText = f.render(RuntimeVariables.CurrentTypingTaskNumbers, True, (0, 0, 0))
    textWidth, textHeight = f.size(RuntimeVariables.CurrentTypingTaskNumbers)
    x = (Constants.TopLeftCornerOfTypingTaskWindow.X + ExperimentSettings.TaskWindowSize.X / 2) - (textWidth / 2)
    y = (Constants.TopLeftCornerOfTypingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y / 2) - (textHeight / 2)
    RuntimeVariables.Screen.blit(typingTaskNumberText, (x, y))


def drawTrackingWindow():
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
    drawCircles(bg)
    RuntimeVariables.Screen.blit(bg, (Constants.TopLeftCornerOfTrackingTaskWindow.X, Constants.TopLeftCornerOfTrackingTaskWindow.Y))
    # Show the number of points above the tracking circle
    displayForNormalTasks = RuntimeVariables.CurrentTaskType == TaskTypes.DualTask and RuntimeVariables.DisplayScoreForNormalTrials
    displayForPracticeTasks = RuntimeVariables.CurrentTaskType == TaskTypes.PracticeDualTask and RuntimeVariables.DisplayScoreForPracticeTrials
    if not RuntimeVariables.ParallelDualTasks and (displayForNormalTasks or displayForPracticeTasks):
        drawDualTaskScoreAboveCircle()


def drawCursor():
    newCursorLocation = Vector2D(RuntimeVariables.CursorCoordinates.X - (ExperimentSettings.CursorSize.X / 2), RuntimeVariables.CursorCoordinates.Y - (ExperimentSettings.CursorSize.Y / 2))
    newCursor = pygame.Surface((ExperimentSettings.CursorSize.X, ExperimentSettings.CursorSize.Y)).convert()
    newCursor.fill(RuntimeVariables.CurrentCursorColor)
    RuntimeVariables.Screen.blit(newCursor, (newCursorLocation.X, newCursorLocation.Y))  # blit puts something new on the screen


def drawDualTaskScoreAboveCircle():
    """Draws the visit score above the circle for switching dual tasks"""
    intermediateMessage = f"{int(RuntimeVariables.VisitScore)} Punkte"
    fontsize = ExperimentSettings.GeneralFontSize
    f = pygame.font.Font(None, fontsize)
    textWidth, textHeight = f.size(intermediateMessage)
    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + (ExperimentSettings.TaskWindowSize.X / 2) - (textWidth / 2)
    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + 10
    printTextOverMultipleLines(intermediateMessage, Vector2D(x, y))


def ApplyRewardForTypingTaskScores():
    """
    For switching dual tasks: Calculates a reward for the user score. If the cursor is outside of the circle, the possible reward is reduced.
    This function is called at the end of a dual task trial or when switching from typing to tracking window.
    """
    # This is the typing reward and the typing penalty
    gainFormula = (RuntimeVariables.CorrectlyTypedDigitsVisit * RuntimeVariables.TypingRewardCorrectDigit) - (RuntimeVariables.IncorrectlyTypedDigitsVisit * RuntimeVariables.TypingPenaltyIncorrectDigit)

    # If Cursor is inside the circle, apply the full reward
    applyPenalty = isCursorOutsideCircle() and RuntimeVariables.Penalty != Penalty.NoPenalty
    if not applyPenalty:
        RuntimeVariables.VisitScore = gainFormula
    # If Cursor is outside of the circle, reduce the reward (tracking penalty)
    else:
        if RuntimeVariables.Penalty == Penalty.LoseAmount:
            # reduce the reward by an amount, e.g. 500 ("lose500")
            RuntimeVariables.VisitScore = gainFormula - RuntimeVariables.PenaltyAmount
        elif RuntimeVariables.Penalty == Penalty.LoseAll:
            # lose all points by setting the score to 0
            RuntimeVariables.VisitScore = 0
        elif RuntimeVariables.Penalty == Penalty.LoseHalf:
            # reduce the reward by the half
            RuntimeVariables.VisitScore = 0.5 * gainFormula

    # add the score for this digit task visit to the overall trial score
    # trial score is used in reportUserScore
    RuntimeVariables.TrialScore += RuntimeVariables.VisitScore

    writeOutputDataFile("updatedVisitScore", "penaltyApplied" if applyPenalty else "NoPenaltyApplied")


def runSingleTaskTypingTrials(isPracticeTrial, numberOfTrials):
    writeLogFile("--> Practice SingleTyping" if isPracticeTrial else "SingleTyping")
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTaskType = TaskTypes.PracticeSingleTyping
        if not RuntimeVariables.ShowOnlyGetReadyMessage:
            DisplayMessage("Nur Tippen\n\n"
                           "In diesen Durchgängen übst du nur die Tippaufgabe.\n"
                           "Kopiere die Ziffern, die dir auf dem Bildschirm angezeigt werden so schnell wie möglich.\n\n"
                           "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n"
                           "(In zukünftigen Durchgängen würdest du dadurch Punkte verlieren.)", 15)
    else:
        RuntimeVariables.CurrentTaskType = TaskTypes.SingleTyping
        if not RuntimeVariables.ShowOnlyGetReadyMessage:
            DisplayMessage("Nur Tippen\n\n"
                           "Kopiere die Ziffern so schnell wie möglich.\n"
                           "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n", 10)

    RuntimeVariables.CurrentTypingTaskNumbersLength = ExperimentSettings.SingleTypingTaskNumbersLength

    print(f"{RuntimeVariables.CurrentTaskType}, total {numberOfTrials} trials")
    for i in range(0, numberOfTrials):
        print(f"Trial {i}")
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0
        RuntimeVariables.CumulatedTrackingScoreForParallelDualTasks = 0

        CountdownMessage(3)
        pygame.event.clear()  # clear all events
        RuntimeVariables.TrackingWindowVisible = False
        RuntimeVariables.TypingWindowVisible = True

        RuntimeVariables.TrackingTaskPresent = False
        RuntimeVariables.TypingTaskPresent = True
        RuntimeVariables.TrialNumber += 1
        RuntimeVariables.TrackingWindowEntryCounter = 0
        RuntimeVariables.TypingWindowEntryCounter = 0

        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))

        RuntimeVariables.StartTimeCurrentTrial = time.time()

        if RuntimeVariables.TypingTaskPresent:
            UpdateTypingTaskString(reset=True)  # generate numbers initially
            RuntimeVariables.EnteredDigitsStr = ""
            RuntimeVariables.DigitPressTimes = [RuntimeVariables.StartTimeCurrentTrial]

            if RuntimeVariables.TypingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeOutputDataFile("trialStart", "-")

        while (time.time() - RuntimeVariables.StartTimeCurrentTrial) < ExperimentSettings.MaxTrialTimeSingleTyping and RuntimeVariables.EnvironmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the tracking task and the typingTask and starts relevant display updates
            if RuntimeVariables.ParallelDualTasks:
                if (not isPracticeTrial and RuntimeVariables.FeedbackMode == FeedbackMode.Live) or (isPracticeTrial and RuntimeVariables.DisplayScoreForPracticeTrials):
                    DisplayLiveFeedbackParallelDualTasks(TaskTypes.SingleTyping)
            pygame.display.flip()
            time.sleep(0.02)

        writeOutputDataFile("trialEnd", "-", endOfTrial=True)

        if not isPracticeTrial and RuntimeVariables.DisplayScoreForNormalTrials:
            if RuntimeVariables.ParallelDualTasks:
                if RuntimeVariables.FeedbackMode == FeedbackMode.AfterTrialsInInterval and ((i + 1) % RuntimeVariables.IntervalForFeedbackAfterTrials == 0 or i == numberOfTrials - 1):
                    DisplayFeedbackParallelDualTasksAfterTrial()
            else:
                DisplayFeedbackSwitchingDualTaskAfterTrial()


def runSingleTaskTrackingTrials(isPracticeTrial, numberOfTrials):
    writeLogFile("--> Practice SingleTracking" if isPracticeTrial else "SingleTracking")
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTaskType = TaskTypes.PracticeSingleTracking
        if not RuntimeVariables.ShowOnlyGetReadyMessage:
            DisplayMessage(
                "Nur Tracking\n\n"
                "In diesen Durchgängen übst du nur die Trackingaufgabe.\n"
                "Du kannst ausprobieren, wie der Joystick funktioniert und sehen, wie schnell der Cursor umherwandert.\n"
                "Der Cursor bewegt sich so lange frei herum, bis du ihn mit dem Joystick bewegst.\n"
                "Denk daran: deine Aufgabe ist es, zu verhindern, dass der Cursor den Kreis verlässt!",
                15)
    else:
        RuntimeVariables.CurrentTaskType = TaskTypes.SingleTracking
        if not RuntimeVariables.ShowOnlyGetReadyMessage:
            DisplayMessage("Nur Tracking\n\n"
                           "Nutze diesen Durchgang, um dich mit der Geschwindigkeit des Cursors vertraut zu machen, \n"
                           "und denk daran den Cursor mit deinem Joystick in der Kreismitte zu halten.",
                           10)

    print(f"{RuntimeVariables.CurrentTaskType}, total {numberOfTrials} trials")
    for i in range(0, numberOfTrials):
        print(f"Trial {i}")
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        CountdownMessage(3)
        pygame.event.clear()
        RuntimeVariables.TrackingWindowVisible = True
        RuntimeVariables.TypingWindowVisible = False
        RuntimeVariables.TrackingTaskPresent = True
        RuntimeVariables.TypingTaskPresent = False
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0
        RuntimeVariables.CumulatedTrackingScoreForParallelDualTasks = 0

        RuntimeVariables.TrialNumber = RuntimeVariables.TrialNumber + 1
        bg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        bg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(bg, (0, 0))

        RuntimeVariables.StartTimeCurrentTrial = time.time()

        RuntimeVariables.TrackingWindowEntryCounter = 0
        RuntimeVariables.TypingWindowEntryCounter = 0
        RuntimeVariables.CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)

        if RuntimeVariables.TrackingTaskPresent:
            RuntimeVariables.JoystickAxis = Vector2D(0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                RuntimeVariables.JoystickObject = pygame.joystick.Joystick(0)
                RuntimeVariables.JoystickObject.init()
            except (pygame.error, NameError):
                pass

            if RuntimeVariables.TrackingWindowVisible:
                openTrackingWindow()
            else:
                closeTrackingWindow()

        writeOutputDataFile("trialStart", "-")

        while ((time.time() - RuntimeVariables.StartTimeCurrentTrial) < ExperimentSettings.MaxTrialTimeSingleTracking) and RuntimeVariables.EnvironmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates

            if RuntimeVariables.ParallelDualTasks:
                if (not isPracticeTrial and RuntimeVariables.FeedbackMode == FeedbackMode.Live) or (isPracticeTrial and RuntimeVariables.DisplayScoreForPracticeTrials):
                    DisplayLiveFeedbackParallelDualTasks(TaskTypes.SingleTracking)

            if RuntimeVariables.TrackingTaskPresent and RuntimeVariables.TrackingWindowVisible:
                updateCursor(0.02)  # calls drawTrackingWindow() and drawCursor()
                writeOutputDataFile("trackingVisible", "-")

        writeOutputDataFile("trialEnd", "-", endOfTrial=True)

        if not isPracticeTrial and RuntimeVariables.DisplayScoreForNormalTrials:
            if RuntimeVariables.ParallelDualTasks:
                if RuntimeVariables.FeedbackMode == FeedbackMode.AfterTrialsInInterval and ((i + 1) % RuntimeVariables.IntervalForFeedbackAfterTrials == 0 or i == numberOfTrials - 1):
                    DisplayFeedbackParallelDualTasksAfterTrial()

        # At the trial end: clear distances for RMSE
        RuntimeVariables.CursorDistancesToMiddle = []


def runDualTaskTrials(isPracticeTrial, numberOfTrials):
    writeLogFile("--> Practice DualTask" if isPracticeTrial else "DualTask")
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTaskType = TaskTypes.PracticeDualTask

        if not RuntimeVariables.ShowOnlyGetReadyMessage:
            message = "Tracking + Tippen (MULTITASKING)\n\n" \
                      "Du übst jetzt beide Aufgaben gleichzeitig!\n\n"
            if not RuntimeVariables.ParallelDualTasks:
                message += "Die Ziffernaufgabe wird dir immer zuerst angezeigt.\n" \
                           "Drücke den Schalter unter deinem Zeigefinger am Joystick, um zu kontrollieren ob der Cursor\n" \
                           "noch innerhalb des Kreises ist.\n" \
                           "Lasse den Schalter wieder los, um zur Ziffernaufgabe zurück zu gelangen.\n" \
                           "Du kannst immer nur eine Aufgabe bearbeiten."
            DisplayMessage(message, 10)

            message = ""
            if RuntimeVariables.DisplayScoreForPracticeTrials:
                message += "Dein Ziel:\n\n" \
                           "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte.\n" \
                           "Fehler beim Tippen führen zu Punkteverlust.\n"
            if not RuntimeVariables.Penalty == Penalty.NoPenalty:
                message += "Pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
            if message:
                DisplayMessage(message, 10)

    # Normal (no practice) trial
    else:
        RuntimeVariables.CurrentTaskType = TaskTypes.DualTask
        if not RuntimeVariables.ShowOnlyGetReadyMessage:
            if RuntimeVariables.DisplayScoreForNormalTrials:
                message = "Dein Ziel:\n\n" \
                          "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte.\n" \
                          "Fehler beim Tippen führen zu Punkteverlust.\n"
                if not RuntimeVariables.Penalty == Penalty.NoPenalty:
                    message += "Aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
                message += "Wichtig: Deine Leistung in diesen Durchgängen zählt für deine Gesamtpunktzahl."
                DisplayMessage(message, 18)
            if not RuntimeVariables.ParallelDualTasks:
                DisplayMessage("Drücke den Schalter unter deinem Zeigefinger, um das Trackingfenster zu öffnen.\n"
                               "Um wieder zurück zur Tippaufgabe zu gelangen, lässt du den Schalter wieder los.\n"
                               "Du kannst immer nur eine Aufgabe bearbeiten.", 15)

    RuntimeVariables.CurrentTypingTaskNumbersLength = 1 if RuntimeVariables.ParallelDualTasks else ExperimentSettings.SingleTypingTaskNumbersLength

    print(f"{RuntimeVariables.CurrentTaskType}, total {numberOfTrials} trials")
    for i in range(0, numberOfTrials):
        print(f"Trial {i}")
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0
        RuntimeVariables.CumulatedTrackingScoreForParallelDualTasks = 0

        CountdownMessage(3)
        pygame.event.clear()  # clear all events

        if RuntimeVariables.DisplayTypingTaskWithinCursor:
            RuntimeVariables.TrackingWindowVisible = True
            RuntimeVariables.TypingWindowVisible = False
        elif RuntimeVariables.ParallelDualTasks:
            RuntimeVariables.TrackingWindowVisible = True
            RuntimeVariables.TypingWindowVisible = True
        else:  # normal dual task with switching
            RuntimeVariables.TrackingWindowVisible = False
            RuntimeVariables.TypingWindowVisible = True

        RuntimeVariables.TrackingTaskPresent = True
        RuntimeVariables.TypingTaskPresent = True

        RuntimeVariables.TrackingWindowEntryCounter = 0
        RuntimeVariables.TypingWindowEntryCounter = 0
        RuntimeVariables.TrialNumber = RuntimeVariables.TrialNumber + 1
        RuntimeVariables.CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)

        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))

        RuntimeVariables.StartTimeCurrentTrial = time.time()

        if RuntimeVariables.TrackingTaskPresent:
            RuntimeVariables.JoystickAxis = Vector2D(0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                RuntimeVariables.JoystickObject = pygame.joystick.Joystick(0)
                RuntimeVariables.JoystickObject.init()
            except (pygame.error, NameError):
                pass

            if RuntimeVariables.TrackingWindowVisible:
                openTrackingWindow()
            else:
                closeTrackingWindow()

        if RuntimeVariables.TypingTaskPresent:
            UpdateTypingTaskString(reset=True)  # generate numbers initially
            RuntimeVariables.EnteredDigitsStr = ""
            RuntimeVariables.DigitPressTimes = [RuntimeVariables.StartTimeCurrentTrial]
            if RuntimeVariables.TypingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeOutputDataFile("trialStart", "-")

        while (time.time() - RuntimeVariables.StartTimeCurrentTrial) < ExperimentSettings.MaxTrialTimeDual and RuntimeVariables.EnvironmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the tracking task and the typingTask and starts relevant display updates

            if RuntimeVariables.ParallelDualTasks and RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible and not RuntimeVariables.DisplayTypingTaskWithinCursor:
                drawTypingWindow()
            if RuntimeVariables.ParallelDualTasks:
                if (not isPracticeTrial and RuntimeVariables.FeedbackMode == FeedbackMode.Live) or (isPracticeTrial and RuntimeVariables.DisplayScoreForPracticeTrials):
                    DisplayLiveFeedbackParallelDualTasks(TaskTypes.DualTask)
            updateCursor(0.02)  # also draws tracking window and typing task in cursor

            if RuntimeVariables.TrackingTaskPresent and RuntimeVariables.TrackingWindowVisible:
                if not RuntimeVariables.ParallelDualTasks:
                    drawCover("typing")

            # When drawing the typing task in cursor, the display update is done in updateCursor(). For switching dual tasks, update must be done here.
            if not (RuntimeVariables.DisplayTypingTaskWithinCursor and RuntimeVariables.ParallelDualTasks):
                pygame.display.flip()  # update display

            if RuntimeVariables.ParallelDualTasks:
                eventMsg = "trackingAndTypingVisible"
            elif RuntimeVariables.TrackingWindowVisible:
                eventMsg = "trackingVisible"
            elif RuntimeVariables.TypingWindowVisible:
                eventMsg = "typingVisible"
            else:
                eventMsg = ""

            writeOutputDataFile(eventMsg, "-")

        RuntimeVariables.VisitEndTime = time.time()
        ApplyRewardForTypingTaskScores()

        writeOutputDataFile("trialEnd", "-", endOfTrial=True)

        if not isPracticeTrial and RuntimeVariables.DisplayScoreForNormalTrials:
            if RuntimeVariables.ParallelDualTasks:
                if RuntimeVariables.FeedbackMode == FeedbackMode.AfterTrialsInInterval and ((i + 1) % RuntimeVariables.IntervalForFeedbackAfterTrials == 0 or i == numberOfTrials - 1):
                    DisplayFeedbackParallelDualTasksAfterTrial()
            else:
                DisplayFeedbackSwitchingDualTaskAfterTrial()

        # At the trial end: clear distances for RMSE
        RuntimeVariables.CursorDistancesToMiddle = []


def ShowStartExperimentScreen():
    drawCanvas()
    location = Vector2D(175, 175)

    message = "Experimentalleiter bitte hier drücken."
    printTextOverMultipleLines(message, Vector2D(location.X, location.Y))
    pygame.display.flip()

    while not checkMouseClicked():  # wait for a mouseclick
        time.sleep(0.25)
    RuntimeVariables.StartTimeCurrentTrial = time.time()


def SetDebuggingSettings():
    """Set settings which are useful for debugging but should NOT be set for actual testing with participants"""
    print("DEBUG MODE IS ACTIVE")
    ExperimentSettings.MaxTrialTimeDual = 5  # make trials end faster
    ExperimentSettings.MaxTrialTimeSingleTracking = 5
    ExperimentSettings.MaxTrialTimeSingleTyping = 5


def ValidateSettings():
    # Avoid a program crash by division by zero
    if RuntimeVariables.FeedbackMode == FeedbackMode.AfterTrialsInInterval and not RuntimeVariables.IntervalForFeedbackAfterTrials > 0:
        raise Exception("RuntimeVariables.IntervalForFeedbackAfterTrials cannot be zero!")


def StartExperiment():
    if ExperimentSettings.DebugMode:
        SetDebuggingSettings()

    ValidateSettings()

    # Sort the circle lists by radius to make getting the typing task numbers work properly
    RuntimeVariables.CirclesSmall.sort(key=lambda circle: circle.Radius, reverse=False)
    RuntimeVariables.CirclesBig.sort(key=lambda circle: circle.Radius, reverse=False)
    RuntimeVariables.CirclesPractice.sort(key=lambda circle: circle.Radius, reverse=False)

    conditions = readParticipantFile()
    initializeOutputFiles()
    RuntimeVariables.StartTimeOfFirstExperiment = time.time()

    pygame.init()
    if ExperimentSettings.DebugMode:  # No fullscreen in debug mode
        RuntimeVariables.Screen = pygame.display.set_mode((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y))
    else:
        RuntimeVariables.Screen = pygame.display.set_mode((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y), pygame.FULLSCREEN)
    pygame.display.set_caption(Constants.Title)

    # verify all conditions before the experiment starts so that the program would crash at the start if it does
    conditionsVerified = []
    for currentCondition in conditions:
        conditionStandardDeviationOfNoise = currentCondition['standardDeviationOfNoise']
        conditionCircleSize = currentCondition['circleSize']
        conditionPenalty = currentCondition['penalty']
        conditionGainCorrectDigit = currentCondition['gainCorrectDigit']

        # noise values are h (high), m (medium) or l (low)
        if conditionStandardDeviationOfNoise == "high":
            standardDeviationOfNoise = ExperimentSettings.CursorNoises["high"]
            noiseMsg = "hoher"
        elif conditionStandardDeviationOfNoise == "medium":
            standardDeviationOfNoise = ExperimentSettings.CursorNoises["medium"]
            noiseMsg = "mittlerer"
        elif conditionStandardDeviationOfNoise == "low":
            standardDeviationOfNoise = ExperimentSettings.CursorNoises["low"]
            noiseMsg = "niedriger"
        else:
            raise Exception("Invalid noise: " + conditionStandardDeviationOfNoise)

        # radius is small or big
        if conditionCircleSize == "small":  # small radius
            if len(RuntimeVariables.CirclesSmall) == 0:
                raise Exception("You tried to run a trial with small circles but you don't have small circle radii defined!")
            radiusCircle = RuntimeVariables.CirclesSmall
        elif conditionCircleSize == "big":
            if len(RuntimeVariables.CirclesBig) == 0:
                raise Exception("You tried to run a trial with big circles but you don't have big circle radii defined!")
            radiusCircle = RuntimeVariables.CirclesBig
        else:
            raise Exception("Invalid circle size: " + conditionCircleSize)

        # only if the fourth digit is specified, define penalty
        penaltyAmount = 0
        if conditionPenalty == "all":
            penalty = Penalty.LoseAll
            penaltyMsg = "alle"
        elif conditionPenalty == "half":
            penalty = Penalty.LoseHalf
            penaltyMsg = "die Hälfte deiner"
        elif conditionPenalty == "none":  # No penalty (don't change score on leaving circle)
            penalty = Penalty.NoPenalty
            penaltyMsg = "-"  # won't be shown in this case
        else:  # else penalty must be a number, e.g. 500 for lose500
            try:
                penaltyAmount = int(conditionPenalty)
                penalty = Penalty.LoseAmount
                penaltyMsg = str(penaltyAmount)
            except:
                raise Exception("Invalid penalty: " + conditionPenalty)

        # Verifying all conditions before the first condition starts avoids errors in the middle of the trials
        conditionsVerified.append({
            "standardDeviationOfNoise": standardDeviationOfNoise,
            "noiseMsg": noiseMsg,
            "radiusCircle": radiusCircle,
            "penalty": penalty,
            "penaltyMsg": penaltyMsg,
            "penaltyAmount": penaltyAmount,
            "conditionGainCorrectDigit": conditionGainCorrectDigit
        })

    if not ExperimentSettings.DebugMode:
        ShowStartExperimentScreen()

    RuntimeVariables.StartTime = time.time()

    if RuntimeVariables.RunPracticeTrials:
        DisplayMessage("Willkommen zum Experiment!\n\n\n"
                       "Wir beginnen mit den Übungsdurchläufen.", 10)

        # do practice trials
        RuntimeVariables.CurrentCircles = RuntimeVariables.CirclesPractice
        RuntimeVariables.StandardDeviationOfNoise = ExperimentSettings.CursorNoisePracticeTrials
        RuntimeVariables.Penalty = RuntimeVariables.PenaltyPracticeTrials
        if RuntimeVariables.PenaltyPracticeTrials == Penalty.LoseAmount:
            RuntimeVariables.PenaltyAmount = 500
        print(f"Practice trial. Penalty: {RuntimeVariables.Penalty}, Noise: {RuntimeVariables.StandardDeviationOfNoise}, Gain: {RuntimeVariables.TypingRewardCorrectDigit}")

        for block in RuntimeVariables.RunningOrder:
            if len(RuntimeVariables.CirclesPractice) == 0 and (block.TaskType == TaskTypes.PracticeSingleTracking or block.TaskType == TaskTypes.PracticeDualTask):
                raise Exception("You tried to run practice trials but you don't have practice circle radii defined!")
            if block.TaskType == TaskTypes.PracticeSingleTracking:
                runSingleTaskTrackingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeSingleTyping:
                runSingleTaskTypingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeDualTask:
                runDualTaskTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)

        msg = "Nun beginnt der Hauppteil und wir testen deine Leistung in den Aufgaben, die du \n"\
              "gerade geübt hast.\n"
        if RuntimeVariables.DisplayScoreForNormalTrials:
            msg += "Versuche im Laufe des Experiments so viele Punkte wie möglich zu gewinnen!"
        DisplayMessage(msg, 10)

    # main experiment loop with verified conditions
    for condition in conditionsVerified:
        RuntimeVariables.BlockNumber = 0
        # set global and local variables
        RuntimeVariables.StandardDeviationOfNoise = condition["standardDeviationOfNoise"]
        noiseMsg = condition["noiseMsg"]
        RuntimeVariables.CurrentCircles = condition["radiusCircle"]
        RuntimeVariables.Penalty = condition["penalty"]
        RuntimeVariables.PenaltyAmount = condition["penaltyAmount"]
        penaltyMsg = condition["penaltyMsg"]
        RuntimeVariables.TypingRewardCorrectDigit = condition["conditionGainCorrectDigit"]
        logText = f"Participant {RuntimeVariables.ParticipantNumber}, Penalty {RuntimeVariables.Penalty}, Noise: {RuntimeVariables.StandardDeviationOfNoise}, Gain: {RuntimeVariables.TypingRewardCorrectDigit}"
        print(logText)
        writeLogFile(logText)

        wasDualTaskInCondition = False
        for block in RuntimeVariables.RunningOrder:
            if block.TaskType == TaskTypes.SingleTracking:
                message = getMessageBeforeTrial(TaskTypes.SingleTracking, noiseMsg, penaltyMsg)
                if not RuntimeVariables.ShowOnlyGetReadyMessage:
                    DisplayMessage(message, 12)
                runSingleTaskTrackingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.SingleTyping:
                message = getMessageBeforeTrial(TaskTypes.SingleTyping, noiseMsg, penaltyMsg)
                if not RuntimeVariables.ShowOnlyGetReadyMessage:
                    DisplayMessage(message, 12)
                runSingleTaskTypingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.DualTask:
                wasDualTaskInCondition = True
                message = getMessageBeforeTrial(TaskTypes.DualTask, noiseMsg, penaltyMsg)
                if not RuntimeVariables.ShowOnlyGetReadyMessage:
                    DisplayMessage(message, 12)
                runDualTaskTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)

        if wasDualTaskInCondition and not RuntimeVariables.ParallelDualTasks and RuntimeVariables.DisplayScoreForNormalTrials:
            DisplayMessage("Bisher hast du: " + str(scipy.sum(RuntimeVariables.DualTaskScoreOverAllConditions)) + " Punkte", 8)

    DisplayMessage("Dies ist das Ende der Studie.", 10)
    quitApp()


def getMessageBeforeTrial(trialType, noiseMsg, penaltyMsg):
    message = "NEUER BLOCK: \n\n\n"
    if trialType in [TaskTypes.SingleTracking, TaskTypes.DualTask]:
        message += f"In den folgenden Durchgängen bewegt sich der Cursor mit {noiseMsg} Geschwindigkeit. \n"

    # If the GUI option about showing messages is deactivated, no information about points shall be displayed
    if not RuntimeVariables.DisplayScoreForNormalTrials:
        if trialType == TaskTypes.DualTask:
            message += "Tippe mit deiner linken Hand so viele Ziffern wie möglich, aber achte darauf, \ndass der Cursor den Kreis nicht verlässt.\n"
        elif trialType == TaskTypes.SingleTracking:
            message += "Achte darauf, dass der Cursor den Kreis nicht verlässt.\n"
        elif trialType == TaskTypes.SingleTyping:
            message += "Tippe mit deiner linken Hand so viele Ziffern wie möglich.\n"
        return message

    # The number of points to be won by typing should always be shown
    if trialType in [TaskTypes.SingleTyping, TaskTypes.DualTask]:
        message += f"Für jede korrekt eingegebene Ziffer bekommst du {RuntimeVariables.TypingRewardCorrectDigit} Punkte. \n"

    if RuntimeVariables.ShowPenaltyRewardNoise:
        message2 = "Achtung: "
        append = False
        if trialType in [TaskTypes.DualTask, TaskTypes.SingleTyping]:
            message2 += f"Bei jeder falsch eingetippten Ziffer verlierst du {RuntimeVariables.TypingPenaltyIncorrectDigit} Punkte. \n"
            append = True
        if trialType in [TaskTypes.DualTask, TaskTypes.SingleTracking] and RuntimeVariables.Penalty != Penalty.NoPenalty:
            message2 += f"Wenn der Cursor den Kreis verlässt, verlierst du {penaltyMsg} deiner Punkte."
            append = True
        if append:
            message += message2

    elif not RuntimeVariables.ShowPenaltyRewardNoise:
        if (trialType == TaskTypes.DualTask and RuntimeVariables.Penalty == Penalty.NoPenalty) or trialType == TaskTypes.SingleTyping:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern."
        elif trialType == TaskTypes.DualTask:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern und wenn der Cursor den Kreis verlässt."
        elif trialType == TaskTypes.SingleTracking and RuntimeVariables.Penalty != Penalty.NoPenalty:
            message += "Achtung: Du verlierst Punkte wenn der Cursor den Kreis verlässt."
    return message


def WriteLinesToCzvFile(filename, lines):
    """Expects lines to be a list of lists"""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(lines)


def readCsvFile(filePath):
    """
    Reads a multi-line CSV file separated with ;
    """
    f = open(filePath, 'r')
    individualLines = f.read().split('\n')
    f.close()
    lines = list(map(lambda x: x.split(';'), individualLines))  # split all elements
    return [i for i in lines if [j for j in i if j != '']]  # filter out empty lines


def readParticipantFile():
    """
    Loads the conditions from the participant csv file.
    :returns A list of dictionaries
    """
    filename = f'participant_{RuntimeVariables.ParticipantNumber}.csv'
    try:
        lines = readCsvFile(filename)
    except:
        raise Exception(f"Could not read {filename}")
    conditions = []
    for line in lines:
        try:
            if line[0] == "StandardDeviationOfNoise":  # skip first column title line
                continue
            conditions.append({
                'standardDeviationOfNoise': line[0],
                'circleSize': line[1],
                'penalty': line[2],
                'gainCorrectDigit': int(line[3])
            })
        except:
            raise Exception(f"Error in {filename} with line: {line}")
    return conditions


def initializeOutputFiles():
    """
    Set the participant condition. Initialize the output files
    """
    outputText = \
        "SubjectNr" + ";" \
        "RadiusCircle" + ";" \
        "StandardDeviationOfNoise" + ";" \
        "CurrentTime" + ";" \
        "TrialTime" + ";" \
        "VisitTime" + ";" \
        "BlockNumber" + ";" \
        "TrialNumber" + ";" \
        "Experiment" + ";" \
        "TrackingTaskPresent" + ";" \
        "TypingTaskPresent" + ";" \
        "TrackingWindowVisible" + ";" \
        "TypingWindowVisible" + ";" \
        "TrackingWindowEntryCounter" + ";" \
        "TypingWindowEntryCounter" + ";" \
        "RMSE" + ";" \
        "LengthPathTrackedPixel" + ";" \
        "CursorCoordinatesX" + ";" \
        "CursorCoordinatesY" + ";" \
        "JoystickAxisX" + ";" \
        "JoystickAxisY" + ";" \
        "EnteredDigits" + ";" \
        "EnteredDigitsLength" + ";" \
        "CurrentTypingTaskNumbers" + ";" \
        "GeneratedTypingTaskNumberLength" + ";" \
        "NumberOfCircleExits" + ";" \
        "TrialScore" + ";" \
        "VisitScore" + ";" \
        "CorrectDigitsVisit" + ";" \
        "IncorrectDigitsVisit" + ";" \
        "IncorrectDigitsTrial" + ";" \
        "OutsideRadius" + ";" \
        "TypingRewardCorrectDigit" + ";" \
        "TypingScoreParallelSetup" + ";" \
        "TrackingScoreParallelSetup" + ";" \
        "CombinedScoreParallelSetup" + ";" \
        "EventMessage1" + ";" \
        "EventMessage2" + "\n"

    timestamp = time.strftime("%Y-%m-%d_%H-%M")
    dataFileName = "participant_" + str(RuntimeVariables.ParticipantNumber) + "_data_" + timestamp + ".csv"
    RuntimeVariables.OutputDataFile = open(dataFileName, 'w')  # contains the user data
    RuntimeVariables.OutputDataFile.write(outputText)
    RuntimeVariables.OutputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFile.fileno())

    summaryFileName = "participant_" + str(RuntimeVariables.ParticipantNumber) + "_data_lastTrialEntry_" + timestamp + ".csv"
    RuntimeVariables.OutputDataFileTrialEnd = open(summaryFileName, 'w')  # contains the user data
    RuntimeVariables.OutputDataFileTrialEnd.write(outputText)
    RuntimeVariables.OutputDataFileTrialEnd.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFileTrialEnd.fileno())


def writeOutputDataFile(eventMessage1, eventMessage2, endOfTrial=False):
    currentTime = time.time() - RuntimeVariables.StartTimeOfFirstExperiment  # this is an absolute time, that always increases (necessary to syncronize with eye-tracking)
    currentTime = scipy.special.round(currentTime * 10000) / 10000

    trialTime = time.time() - RuntimeVariables.StartTimeCurrentTrial  # this is a local time (reset at the start of each trial) in seconds
    trialTime = scipy.special.round(trialTime * 10000) / 10000

    if not RuntimeVariables.TrackingTaskPresent:
        outputCursorCoordinateX = "-"
        outputCursorCoordinateY = "-"
        outputJoystickAxisX = "-"
        outputJoystickAxisY = "-"
    else:
        outputCursorCoordinateX = scipy.special.round(RuntimeVariables.CursorCoordinates.X * 100) / 100
        outputCursorCoordinateY = scipy.special.round(RuntimeVariables.CursorCoordinates.Y * 100) / 100
        outputJoystickAxisX = scipy.special.round(RuntimeVariables.JoystickAxis.X * 1000) / 1000
        outputJoystickAxisY = scipy.special.round(RuntimeVariables.JoystickAxis.Y * 1000) / 1000

    if RuntimeVariables.TypingTaskPresent:
        outputEnteredDigitsStr = RuntimeVariables.EnteredDigitsStr
        outputEnteredDigitsLength = len(RuntimeVariables.EnteredDigitsStr)
        outputGeneratedTypingTaskNumbers = RuntimeVariables.CurrentTypingTaskNumbers
        outputGeneratedTypingTaskNumbersLength = len(RuntimeVariables.CurrentTypingTaskNumbers)
    else:
        outputEnteredDigitsStr = "-"
        outputEnteredDigitsLength = "-"
        outputGeneratedTypingTaskNumbers = "-"
        outputGeneratedTypingTaskNumbersLength = "-"

    if RuntimeVariables.CurrentTaskType == TaskTypes.DualTask or RuntimeVariables.CurrentTaskType == TaskTypes.PracticeDualTask:
        visitTime = time.time() - RuntimeVariables.VisitStartTime
    else:
        visitTime = "-"

    circleRadii = list(map(lambda circle: circle.Radius, RuntimeVariables.CurrentCircles))
    currentTask = str(RuntimeVariables.CurrentTaskType).replace("TaskType.", "")

    scores = CalculateFeedbackParallelDualTasks() if RuntimeVariables.ParallelDualTasks else ["-", "-", "-"]
    typingScore = scores[0]
    trackingScore = scores[1]
    combinedScore = scores[2]

    outputText = \
        str(RuntimeVariables.ParticipantNumber) + ";" + \
        str(circleRadii) + ";" + \
        str(RuntimeVariables.StandardDeviationOfNoise) + ";" + \
        str(currentTime) + ";" + \
        str(trialTime) + ";" + \
        str(visitTime) + ";" + \
        str(RuntimeVariables.BlockNumber) + ";" + \
        str(RuntimeVariables.TrialNumber) + ";" + \
        str(currentTask) + ";" + \
        str(RuntimeVariables.TrackingTaskPresent) + ";" + \
        str(RuntimeVariables.TypingTaskPresent) + ";" + \
        str(RuntimeVariables.TrackingWindowVisible) + ";" + \
        str(RuntimeVariables.TypingWindowVisible) + ";" + \
        str(RuntimeVariables.TrackingWindowEntryCounter) + ";" + \
        str(RuntimeVariables.TypingWindowEntryCounter) + ";" + \
        str(calculateRmse()) + ";" + \
        str(RuntimeVariables.LengthOfPathTracked) + ";" + \
        str(outputCursorCoordinateX) + ";" + \
        str(outputCursorCoordinateY) + ";" + \
        str(outputJoystickAxisX) + ";" + \
        str(outputJoystickAxisY) + ";" + \
        str(outputEnteredDigitsStr) + ";" + \
        str(outputEnteredDigitsLength) + ";" + \
        str(outputGeneratedTypingTaskNumbers) + ";" + \
        str(outputGeneratedTypingTaskNumbersLength) + ";" + \
        str(RuntimeVariables.NumberOfCircleExits) + ";" + \
        str(RuntimeVariables.TrialScore) + ";" + \
        str(RuntimeVariables.VisitScore) + ";" + \
        str(RuntimeVariables.CorrectlyTypedDigitsVisit) + ";" + \
        str(RuntimeVariables.IncorrectlyTypedDigitsVisit) + ";" + \
        str(RuntimeVariables.IncorrectlyTypedDigitsTrial) + ";" + \
        str(isCursorOutsideCircle()) + ";" + \
        str(RuntimeVariables.TypingRewardCorrectDigit) + ";" + \
        str(typingScore) + ";" + \
        str(trackingScore) + ";" + \
        str(combinedScore) + ";" + \
        str(eventMessage1) + ";" + \
        str(eventMessage2) + "\n"

    if endOfTrial:
        RuntimeVariables.OutputDataFileTrialEnd.write(outputText)
        RuntimeVariables.OutputDataFileTrialEnd.flush()
        # typically the above line would do. however this is used to ensure that the file is written
        os.fsync(RuntimeVariables.OutputDataFileTrialEnd.fileno())

    RuntimeVariables.OutputDataFile.write(outputText)
    RuntimeVariables.OutputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFile.fileno())


def quitApp(message=None):
    if message:
        print(message)
    RuntimeVariables.EnvironmentIsRunning = False
    pygame.display.quit()
    pygame.quit()
    try:
        if RuntimeVariables.OutputDataFile:
            RuntimeVariables.OutputDataFile.close()
        if RuntimeVariables.OutputDataFileTrialEnd:
            RuntimeVariables.OutputDataFileTrialEnd.close()
    except NameError:
        pass
    sys.exit()


def getFunctionName():
    return inspect.stack()[1][3]


class FeedbackMode(Enum):
    Live = 1
    AfterTrialsInInterval = 2


def DrawGui():
    tkWindow = Tk()
    tkWindow.title(Constants.Title)

    ### Frames for input of Blocks consisting of tasks and trials
    frameLeft = Frame(tkWindow)
    frameLeft.grid(row=0, column=0)
    frameRight = Frame(tkWindow)
    frameRight.grid(row=0, column=1)

    frameBlocks = Frame(frameLeft, highlightbackground="black", highlightthickness=1)
    frameBlocks.grid(row=0, column=0)
    frameBlockListBox = Frame(frameBlocks)
    frameBlockListBox.grid(row=1, column=0)
    frameBlockButtons = Frame(frameBlocks)
    frameBlockButtons.grid(row=1, column=1)

    frameOptions = Frame(frameLeft, highlightbackground="black", highlightthickness=1)
    frameOptions.grid(row=1, column=0)

    frameBottom = Frame(frameLeft)
    frameBottom.grid(row=2, column=0)

    frameCircles = Frame(frameRight, highlightbackground="black", highlightthickness=1)
    frameCircles.grid(row=0, column=0)

    # Listbox and Delete button
    listBoxBlocks = Listbox(frameBlockListBox, width=25)
    listBoxBlocks.grid(row=0, column=0)
    btnDeleteBlock = Button(frameBlockListBox, text="Entfernen", command=lambda: listBoxBlocks.delete(listBoxBlocks.curselection()[0]))
    btnDeleteBlock.grid(row=1, column=0)

    # Blocks: Labels, Inputs and Buttons
    Label(frameBlocks, text="Eingabe von Blocks und Trials").grid(row=0, column=0)
    Label(frameBlockButtons, text="Anzahl Trials:").grid(row=0, column=0)
    txNumTrials = Text(frameBlockButtons, height=1, width=2)
    txNumTrials.grid(row=0, column=1)
    row = 1
    for btn in [("Übung Tracking", TaskTypes.PracticeSingleTracking), ("Übung Typing", TaskTypes.PracticeSingleTyping), ("Übung DualTask", TaskTypes.PracticeDualTask),
                ("Tracking", TaskTypes.SingleTracking), ("Typing", TaskTypes.SingleTyping), ("DualTask", TaskTypes.DualTask)]:
        btnDelete = Button(frameBlockButtons, text=btn[0], command=lambda btn=btn: CreateBlockListEntry(listBoxBlocks, buttonTitle=btn[0], taskType=btn[1], numTrials=txNumTrials.get("1.0", END)))
        btnDelete.grid(row=row, column=0)
        row += 1

    ### Create option checkboxes
    frameInputOptions = Frame(frameOptions)
    frameInputOptions.grid(row=0, column=0)
    Label(frameInputOptions, text="Probandennummer").grid(row=0, column=0)
    txPersonNumber = Text(frameInputOptions, height=1, width=2)
    txPersonNumber.grid(row=0, column=1)

    runPracticeTrials = IntVar()
    chkRunPracticeTrials = Checkbutton(frameOptions, text="Übungs-Trials durchführen", variable=runPracticeTrials)
    chkRunPracticeTrials.grid(row=1, column=0)
    showPenaltyRewardNoise = IntVar()
    chkShowPenaltyRewardNoise = Checkbutton(frameOptions, text="Penalty-Info vor dem Experiment anzeigen", variable=showPenaltyRewardNoise)
    chkShowPenaltyRewardNoise.grid(row=2, column=0)

    disableTypingScoreOutside = IntVar()
    dtsoTxt = "Wenn sich im DualTask der Cursor ausserhalb des Kreises befindet,\n sollen im TypingTask korrekte Eingaben nicht gezählt werden"
    chkDisableTypingScoreOutside = Checkbutton(frameOptions, text=dtsoTxt, variable=disableTypingScoreOutside)
    chkDisableTypingScoreOutside.grid(row=3, column=0)

    displayScoreNormalTrials = IntVar()
    txt = "Punktestand bei normalen Trials anzeigen \n(ausser wenn Penalty auf none gesetzt ist)"
    chkDisplayScoreNormalTrials = Checkbutton(frameOptions, text=txt, variable=displayScoreNormalTrials)
    chkDisplayScoreNormalTrials.grid(row=4, column=0)

    displayScorePracticeTrials = IntVar()
    txt = "Punktestand bei Übungs-Trials anzeigen \n(ausser wenn Penalty auf none gesetzt ist)"
    chkDisplayScorePracticeTrials = Checkbutton(frameOptions, text=txt, variable=displayScorePracticeTrials)
    chkDisplayScorePracticeTrials.grid(row=5, column=0)

    framePracticePenalty = Frame(frameOptions)
    framePracticePenalty.grid(row=6, column=0)
    Label(framePracticePenalty, text="Tracking Penalty für Übungs-Trials \n(bei LoseAmount: 500)").grid(row=0, column=0)
    practiceTrackingPenaltyOptions = [Penalty.NoPenalty, Penalty.LoseAll, Penalty.LoseHalf, Penalty.LoseAmount]
    practiceTrackingPenalty = StringVar(framePracticePenalty)
    practiceTrackingPenalty.set(practiceTrackingPenaltyOptions[0])  # default value
    drpPracticeTrackingPenalty = OptionMenu(framePracticePenalty, practiceTrackingPenalty, *practiceTrackingPenaltyOptions)
    drpPracticeTrackingPenalty.grid(row=0, column=1)

    frameParallelSetup = Frame(frameOptions, highlightbackground="black", highlightthickness=1)
    frameParallelSetup.grid(row=7, column=0)

    parallelDualTasks = IntVar()
    chkParallelDualTasks = Checkbutton(frameParallelSetup, text="Parallele DualTasks", variable=parallelDualTasks)
    chkParallelDualTasks.grid(row=0, column=0)
    typingTaskInCursor = IntVar()
    chkTypingTaskInCursor = Checkbutton(frameParallelSetup, text="Typing Task in Cursor", variable=typingTaskInCursor)
    chkTypingTaskInCursor.grid(row=1, column=0)

    frameParallelFeedback = Frame(frameParallelSetup)
    frameParallelFeedback.grid(row=2, column=0)
    Label(frameParallelFeedback, text="Anzeige Feedback bei\nparallelem DualTask Setup:").grid(row=0, column=0)
    parallelFeedbackOptions = [FeedbackMode.Live, FeedbackMode.AfterTrialsInInterval]
    parallelFeedback = StringVar(frameParallelFeedback)
    parallelFeedback.set(parallelFeedbackOptions[0])  # default value
    drpParallelFeedback = OptionMenu(frameParallelFeedback, parallelFeedback, *parallelFeedbackOptions)
    drpParallelFeedback.grid(row=0, column=1)

    frameInterval = Frame(frameParallelSetup)
    frameInterval.grid(row=3, column=0)
    Label(frameInterval, text="Intervall für Feedback nach Trials:").grid(row=0, column=0)
    txFeedbackInterval = Text(frameInterval, height=1, width=2)
    txFeedbackInterval.grid(row=0, column=1)

    showOnlyGetReadyMessage = IntVar()
    chkShowOnlyGetReadyMessage = Checkbutton(frameParallelSetup, text="Nur Instruktion zeigen: \"Mach dich bereit\"", variable=showOnlyGetReadyMessage)
    chkShowOnlyGetReadyMessage.grid(row=4, column=0)


    ### Create three input forms for big, small and practice circles
    currentColumn = 0
    listBoxCirclesBig = Listbox()
    listBoxCirclesSmall = Listbox()
    listBoxCirclesPractice = Listbox()
    for circleType in [("circlePractice", "ÜBUNGS"), ("circleBig", "GROßE"), ("circleSmall", "KLEINE")]:
        circleIdentifier = circleType[0]
        circleTextWord = circleType[1]

        # Circle: Frames
        frameCircle = Frame(frameCircles, highlightbackground="black", highlightthickness=1)
        frameCircle.grid(row=currentColumn, column=0)
        frameCircleInputs = Frame(frameCircle)
        frameCircleInputs.grid(row=1, column=0)
        frameCirclesListBox = Frame(frameCircle)
        frameCirclesListBox.grid(row=1, column=1)
        frameCircleButtons = Frame(frameCircle)
        frameCircleButtons.grid(row=2, column=0)

        # Circles: Labels, Buttons and ListBox
        Label(frameCircle, text=f"Eingabe der Kreisradii für {circleTextWord} Kreise").grid(row=0, column=0)
        listBoxCircles = Listbox(frameCirclesListBox, width=100, height=10)
        listBoxCircles.grid(row=0, column=0)
        btnDeleteCircle = Button(frameCirclesListBox, text="Entfernen", command=lambda listBoxCircles=listBoxCircles: listBoxCircles.delete(listBoxCircles.curselection()[0]))
        btnDeleteCircle.grid(row=1, column=0)

        # Input fields for Circle attributes
        Label(frameCircleInputs, text="Radius:").grid(row=0, column=0)
        txRadiusInput = Text(frameCircleInputs, height=1, width=4)
        txRadiusInput.grid(row=0, column=1)
        Label(frameCircleInputs, text="Typing Task Ziffern:").grid(row=1, column=0)
        txTypingTaskNumbers = Text(frameCircleInputs, height=1, width=14)
        txTypingTaskNumbers.grid(row=1, column=1)
        Label(frameCircleInputs, text="Farbe Kreis innen (R,G,B):").grid(row=2, column=0)
        txInnerCircleColor = Text(frameCircleInputs, height=1, width=14)  # Enter a RGB color, e.g. (255, 0, 0) for Red
        txInnerCircleColor.grid(row=2, column=1)
        Label(frameCircleInputs, text="Farbe Kreis Rahmen (R,G,B):").grid(row=3, column=0)
        txBorderColor = Text(frameCircleInputs, height=1, width=14)
        txBorderColor.grid(row=3, column=1)
        currentColumn += 1
        btnAddCircle = Button(frameCircleInputs, text="Kreis hinzufügen",
                              command=lambda listBoxCircles=listBoxCircles, circleIdentifier=circleIdentifier, txRadiusInput=txRadiusInput, txTypingTaskNumbers=txTypingTaskNumbers, txInnerCircleColor=txInnerCircleColor, txBorderColor=txBorderColor:
                              CreateCircleListEntry(listBoxCircles, circleIdentifier, txRadiusInput.get("1.0", END), txTypingTaskNumbers.get("1.0", END), txInnerCircleColor.get("1.0", END), txBorderColor.get("1.0", END)))
        btnAddCircle.grid(row=4, column=0)

        # To load the circles from settings file, save the listboxes for later access
        if circleIdentifier == "circleBig":
            listBoxCirclesBig = listBoxCircles
        elif circleIdentifier == "circleSmall":
            listBoxCirclesSmall = listBoxCircles
        elif circleIdentifier == "circlePractice":
            listBoxCirclesPractice = listBoxCircles

    # Bottom Frame
    btnStart = Button(frameBottom, text="Starten",
                      command=lambda: ParseAndSaveInputs(tkWindow, listBoxBlocks, listBoxCirclesBig, listBoxCirclesSmall, listBoxCirclesPractice, txPersonNumber,
                                         parallelDualTasks, typingTaskInCursor, runPracticeTrials, showPenaltyRewardNoise, disableTypingScoreOutside,
                                         displayScoreNormalTrials, displayScorePracticeTrials, practiceTrackingPenalty, parallelFeedback, txFeedbackInterval,
                                         showOnlyGetReadyMessage))
    btnStart.grid(row=5, column=0)

    # Finally load settings from file if present
    settings = LoadSettingsFromFile()
    if settings:
        for block in settings.Blocks:
            CreateBlockListEntry(listBoxBlocks, buttonTitle=block[0], taskType=block[1], numTrials=block[2])
        for circle in settings.Circles:
            circleIdentifier = circle[0]
            if circleIdentifier == "circleBig":
                listBoxCircles = listBoxCirclesBig
            elif circleIdentifier == "circleSmall":
                listBoxCircles = listBoxCirclesSmall
            elif circleIdentifier == "circlePractice":
                listBoxCircles = listBoxCirclesPractice
            CreateCircleListEntry(listBoxCircles, circleType=circleIdentifier, radius=circle[1], typingTaskNumbers=circle[2], innerCircleColor=circle[3], borderColor=circle[4])
        for key, value in settings.Options.items():
            if key == "ParallelDualTasks" and value == "1":
                chkParallelDualTasks.select()
            if key == "DisplayTypingTaskWithinCursor" and value == "1":
                chkTypingTaskInCursor.select()
            if key == "RunPracticeTrials" and value == "1":
                chkRunPracticeTrials.select()
            if key == "ShowPenaltyRewardNoise" and value == "1":
                chkShowPenaltyRewardNoise.select()
            if key == "DisableTypingScoreOutside" and value == "1":
                chkDisableTypingScoreOutside.select()
            if key == "DisplayScoreForNormalTrials" and value == "1":
                chkDisplayScoreNormalTrials.select()
            if key == "DisplayScoreForPracticeTrials" and value == "1":
                chkDisplayScorePracticeTrials.select()
            if key == "PracticeTrackingPenalty":
                for listEntryPenalty in practiceTrackingPenaltyOptions:
                    if str(listEntryPenalty) == value:
                        practiceTrackingPenalty.set(listEntryPenalty)
            if key == "ParallelFeedback":
                for listEntryParallelFeedback in parallelFeedbackOptions:
                    if str(listEntryParallelFeedback) == value:
                        parallelFeedback.set(listEntryParallelFeedback)
            if key == "FeedbackInterval":
                txFeedbackInterval.insert(END, value)
            if key == "ShowOnlyGetReadyMessage" and value == "1":
                chkShowOnlyGetReadyMessage.select()
    tkWindow.mainloop()


def CreateBlockListEntry(listBox, buttonTitle, taskType, numTrials):
    try:
        numTrialsParsed = int(numTrials)
    except ValueError:
        return
    if not numTrialsParsed > 0:
        return
    listBoxText = f"{buttonTitle}, {numTrialsParsed} Trial(s)"
    RuntimeVariables.DictTrialListEntries[listBoxText] = (buttonTitle, str(taskType), numTrialsParsed)
    listBox.insert(END, listBoxText)


def CreateCircleListEntry(listBox, circleType, radius, typingTaskNumbers, innerCircleColor, borderColor):
    try:
        radiusParsed = int(radius)
    except ValueError:
        return
    if not radiusParsed > 0:
        return
    circleType = circleType.strip()
    radius = radius.strip()
    typingTaskNumbers = typingTaskNumbers.strip()
    innerCircleColor = innerCircleColor.strip()  # RGB values are not validated for correctness yet
    borderColor = borderColor.strip()
    listBoxText = f"{circleType} Radius={radiusParsed}, DualTaskTypingNumbers={typingTaskNumbers}, InnerCircleColor={innerCircleColor}, BorderColor={borderColor}"
    if listBoxText in RuntimeVariables.DictTrialListEntries:
        raise Exception("Circle list entry is not unique")
    RuntimeVariables.DictTrialListEntries[listBoxText] = (circleType, radius, typingTaskNumbers, innerCircleColor, borderColor)
    listBox.insert(END, listBoxText)


class SettingsFile:
    Blocks = []
    Circles = []
    Options = {}


def LoadSettingsFromFile():
    if not path.exists(Constants.SettingsFilename):
        return
    csvFileContent = readCsvFile(Constants.SettingsFilename)
    settingsFile = SettingsFile()
    for line in csvFileContent:
        key = line[0]
        # Parse Blocks
        if key == "Block":
            buttonTitle = line[1]
            taskType = line[2]
            numTrials = line[3]
            settingsFile.Blocks.append((buttonTitle, taskType, numTrials))
        if key == "Circle":
            circleType = line[1]
            radius = line[2]
            typingTaskNumbers = line[3]
            innerCircleColor = line[4]
            borderColor = line[5]
            settingsFile.Circles.append((circleType, radius, typingTaskNumbers, innerCircleColor, borderColor))
        if key == "ParallelDualTasks":
            settingsFile.Options[key] = line[1]
        if key == "DisplayTypingTaskWithinCursor":
            settingsFile.Options[key] = line[1]
        if key == "RunPracticeTrials":
            settingsFile.Options[key] = line[1]
        if key == "ShowPenaltyRewardNoise":
            settingsFile.Options[key] = line[1]
        if key == "DisableTypingScoreOutside":
            settingsFile.Options[key] = line[1]
        if key == "DisplayScoreForNormalTrials":
            settingsFile.Options[key] = line[1]
        if key == "DisplayScoreForPracticeTrials":
            settingsFile.Options[key] = line[1]
        if key == "PracticeTrackingPenalty":
            settingsFile.Options[key] = line[1]
        if key == "ParallelFeedback":
            settingsFile.Options[key] = line[1]
        if key == "FeedbackInterval":
            settingsFile.Options[key] = line[1]
        if key == "ShowOnlyGetReadyMessage":
            settingsFile.Options[key] = line[1]
    return settingsFile


def ParseAndSaveInputs(tkWindow, listBoxBlocks, listBoxCirclesBig, listBoxCirclesSmall, listBoxCirclesPractice, txPersonNumber,
                       parallelDualTasks, typingTaskInCursor, runPracticeTrials, showPenaltyRewardNoise, disableTypingScoreOutside,
                       displayScoreNormalTrials, displayScorePracticeTrials, practiceTrackingPenalty, parallelFeedback, txFeedbackInterval,
                       showOnlyGetReadyMessage):
    linesSettingsFile = []
    # Write Blocks
    for listEntryText in listBoxBlocks.get(0, END):
        buttonTitle = RuntimeVariables.DictTrialListEntries[listEntryText][0]
        taskTypeUnparsed = RuntimeVariables.DictTrialListEntries[listEntryText][1]
        taskType = eval(taskTypeUnparsed)  # convert to Enum TaskTypes
        numTrials = int(RuntimeVariables.DictTrialListEntries[listEntryText][2])
        RuntimeVariables.RunningOrder.append(Block(taskType=taskType, numberOfTrials=numTrials))
        linesSettingsFile.append(["Block", buttonTitle, taskType, numTrials])
    # Write Circles
    listBoxCirclesEntries = listBoxCirclesBig.get(0, END) + listBoxCirclesSmall.get(0, END) + listBoxCirclesPractice.get(0, END)
    for listEntryText in listBoxCirclesEntries:
        circleType = RuntimeVariables.DictTrialListEntries[listEntryText][0]
        radius = int(RuntimeVariables.DictTrialListEntries[listEntryText][1])
        typingTaskNumbers = RuntimeVariables.DictTrialListEntries[listEntryText][2]
        innerCircleColor = eval(RuntimeVariables.DictTrialListEntries[listEntryText][3])
        borderColor = eval(RuntimeVariables.DictTrialListEntries[listEntryText][4])
        linesSettingsFile.append(["Circle", circleType, radius, typingTaskNumbers, innerCircleColor, borderColor])
        if circleType == "circleBig":
            RuntimeVariables.CirclesBig.append(Circle(radius, typingTaskNumbers, innerCircleColor, borderColor))
        elif circleType == "circleSmall":
            RuntimeVariables.CirclesSmall.append(Circle(radius, typingTaskNumbers, innerCircleColor, borderColor))
        elif circleType == "circlePractice":
            RuntimeVariables.CirclesPractice.append(Circle(radius, typingTaskNumbers, innerCircleColor, borderColor))

    try:
        RuntimeVariables.ParticipantNumber = str(int(txPersonNumber.get("1.0", END).strip()))
    except:
        print("No Subject number entered")
        return

    # Set Options to RuntimeVariables
    parallelDualTasksEnabled = parallelDualTasks.get()
    if parallelDualTasksEnabled == 1:
        RuntimeVariables.ParallelDualTasks = True
        Constants.OffsetTaskWindowsTop += 20
        Constants.TopLeftCornerOfTypingTaskWindow = Vector2D(Constants.OffsetLeftRight, Constants.OffsetTaskWindowsTop)
        Constants.TopLeftCornerOfTrackingTaskWindow = Vector2D(Constants.OffsetLeftRight + ExperimentSettings.TaskWindowSize.X + ExperimentSettings.SpaceBetweenWindows, Constants.OffsetTaskWindowsTop)

    if typingTaskInCursor.get() == 1:
        RuntimeVariables.DisplayTypingTaskWithinCursor = True
        RuntimeVariables.ParallelDualTasks = True  # also required
        parallelDualTasksEnabled = 1  # save the other option as checked to file
        Constants.OffsetTaskWindowsTop += 20
        Constants.TopLeftCornerOfTypingTaskWindow = Vector2D(Constants.OffsetLeftRight, Constants.OffsetTaskWindowsTop)
        Constants.TopLeftCornerOfTrackingTaskWindow = Vector2D(Constants.OffsetLeftRight + ExperimentSettings.TaskWindowSize.X + ExperimentSettings.SpaceBetweenWindows, Constants.OffsetTaskWindowsTop)
    else:
        RuntimeVariables.DisplayTypingTaskWithinCursor = False

    RuntimeVariables.RunPracticeTrials = True if runPracticeTrials.get() == 1 else False
    RuntimeVariables.ShowPenaltyRewardNoise = True if showPenaltyRewardNoise.get() == 1 else False
    RuntimeVariables.DisableCorrectTypingScoreOutsideCircle = True if disableTypingScoreOutside.get() == 1 else False
    RuntimeVariables.DisplayScoreForNormalTrials = True if displayScoreNormalTrials.get() == 1 else False
    RuntimeVariables.DisplayScoreForPracticeTrials = True if displayScorePracticeTrials.get() == 1 else False

    RuntimeVariables.PenaltyPracticeTrials = Penalty[practiceTrackingPenalty.get().replace("Penalty.", "")]
    RuntimeVariables.FeedbackMode = FeedbackMode[parallelFeedback.get().replace("FeedbackMode.", "")]

    feedbackInterval = txFeedbackInterval.get("1.0", END).strip()
    interval = ""
    try:
        if RuntimeVariables.FeedbackMode != FeedbackMode.AfterTrialsInInterval and not feedbackInterval:  # interval textbox can be empty if not required
            leaveIntervalBoxEmpty = True
        else:
            interval = int(feedbackInterval)
            RuntimeVariables.IntervalForFeedbackAfterTrials = interval
            leaveIntervalBoxEmpty = False
    except:
        print("Invalid interval for parallel dual task feedback entered")
        return

    RuntimeVariables.ShowOnlyGetReadyMessage = True if showOnlyGetReadyMessage.get() == 1 else False

    # Save Options to file
    linesSettingsFile.append(["ParallelDualTasks", parallelDualTasksEnabled])
    linesSettingsFile.append(["DisplayTypingTaskWithinCursor", typingTaskInCursor.get()])
    linesSettingsFile.append(["RunPracticeTrials", runPracticeTrials.get()])
    linesSettingsFile.append(["ShowPenaltyRewardNoise", showPenaltyRewardNoise.get()])
    linesSettingsFile.append(["DisableTypingScoreOutside", disableTypingScoreOutside.get()])
    linesSettingsFile.append(["DisplayScoreForNormalTrials", displayScoreNormalTrials.get()])
    linesSettingsFile.append(["DisplayScoreForPracticeTrials", displayScorePracticeTrials.get()])
    linesSettingsFile.append(["PracticeTrackingPenalty", practiceTrackingPenalty.get()])
    linesSettingsFile.append(["ParallelFeedback", parallelFeedback.get()])
    linesSettingsFile.append(["FeedbackInterval", interval if not leaveIntervalBoxEmpty else ""])
    linesSettingsFile.append(["ShowOnlyGetReadyMessage", showOnlyGetReadyMessage.get()])

    WriteLinesToCzvFile(Constants.SettingsFilename, linesSettingsFile)
    RuntimeVariables.EnvironmentIsRunning = True
    tkWindow.quit()


def writeLogFile(text):
    f = open("messageLog.txt", "a+")
    f.write("################################\n\n" + text + "\n\n")
    f.close()


if __name__ == '__main__':
    try:
        DrawGui()
        if RuntimeVariables.EnvironmentIsRunning:  # check to avoid parsing incomplete form data on closing UI
            StartExperiment()
    except Exception as e:
        stack = traceback.format_exc()
        with open("Error_Logfile.txt", "a") as log:
            log.write(f"\n{datetime.datetime.now()} {str(e)}   {str(stack)} \n")
            print(str(e))
            print(str(stack))
            print("PLEASE CHECK Error_Logfile.txt, the error is logged there!")
