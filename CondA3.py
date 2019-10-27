# coding=utf-8
#############################
#  Multitasking experiment: Typing digits (keyboard) while tracking (joystick)
#  Developed by Dietmar Sach (dsach@mail.de) for the Institute of Sport Science of the University of Augsburg
#  Based on a script made by Christian P. Janssen, c.janssen@ucl.ac.uk December 2009 - March 2010
#############################
import inspect
import os
import random
import sys
import time
import traceback
import math
import pygame
import scipy
import scipy.special
import datetime
from enum import Enum


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
    InnerCircleColor = (255, 204, 102) # orange
    BorderColor = (255, 0, 0) # red
    def __init__(self, radius, typingTaskNumbersDualTask, innerCircleColor, borderColor):
        self.Radius = radius
        self.TypingTaskNumbersDualTask = typingTaskNumbersDualTask
        self.InnerCircleColor = innerCircleColor
        self.BorderColor = borderColor


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
    # Configure here the order of blocks and the number for trials for each respective.
    # The order is from top to bottom. Also add optional Practice Tasks here.
    # Use the task type names from class TaskTypes.
    RunningOrder = [
        Block(taskType=TaskTypes.PracticeSingleTracking, numberOfTrials=2),
        Block(taskType=TaskTypes.PracticeSingleTyping, numberOfTrials=2),
        Block(taskType=TaskTypes.PracticeDualTask, numberOfTrials=2),
        Block(taskType=TaskTypes.SingleTracking, numberOfTrials=1),
        Block(taskType=TaskTypes.SingleTyping, numberOfTrials=1),
        Block(taskType=TaskTypes.DualTask, numberOfTrials=3)
    ]

    # Set to True if for DualTasks, both Tracking and Typing shall be visible simultaneously
    ParallelDualTasks = False
    
    # Set to True if for DualTasks, the typing task window should be hidden and the number is in inside the cursor instead.
    # Also requires ParallelDualTasks to be True.
    DisplayTypingTaskWithinCursor = False

    CirclesSmall = [
        Circle(radius=40, typingTaskNumbersDualTask="12", innerCircleColor=(255, 204, 102), borderColor=(255, 0, 0)),
        Circle(radius=80, typingTaskNumbersDualTask="34", innerCircleColor=(252, 215, 141), borderColor=(255, 0, 0)),
        Circle(radius=100, typingTaskNumbersDualTask="56", innerCircleColor=(250, 228, 185), borderColor=(255, 0, 0))
    ]
    CirclesBig = [
        Circle(radius=80, typingTaskNumbersDualTask="12", innerCircleColor=(255, 204, 102), borderColor=(255, 0, 0)),
        Circle(radius=150, typingTaskNumbersDualTask="34", innerCircleColor=(252, 215, 141), borderColor=(255, 0, 0)),
        Circle(radius=220, typingTaskNumbersDualTask="56", innerCircleColor=(250, 228, 185), borderColor=(255, 0, 0))
    ]
    CirclesPractice = [
        Circle(radius=80, typingTaskNumbersDualTask="12", innerCircleColor=(255, 204, 102), borderColor=(255, 0, 0)),
        Circle(radius=150, typingTaskNumbersDualTask="34", innerCircleColor=(252, 215, 141), borderColor=(255, 0, 0)),
        Circle(radius=220, typingTaskNumbersDualTask="56", innerCircleColor=(250, 228, 185), borderColor=(255, 0, 0))
    ]
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
    CursorNoises = {"high": 5, "medium": 5, "low": 3}  # This is the speed of the cursor movement
    TimeFeedbackIsGiven = 4
    TimeFeedbackIsShown = 4
    BackgroundColorTaskWindows = (255, 255, 255)  # white
    BackgroundColorEntireScreen = (50, 50, 50)  # gray
    CoverColor = (200, 200, 200)  # very light gray
    Fullscreen = True


class Constants:
    Title = "Multitasking 3.0"
    ExperimentWindowSize = Vector2D(1280, 1024)
    OffsetLeftRight = int((ExperimentWindowSize.X - ExperimentSettings.SpaceBetweenWindows - 2 * ExperimentSettings.TaskWindowSize.X) / 2)
    TopLeftCornerOfTypingTaskWindow = Vector2D(OffsetLeftRight, 50)
    TopLeftCornerOfTrackingTaskWindow = Vector2D(OffsetLeftRight + ExperimentSettings.TaskWindowSize.X + ExperimentSettings.SpaceBetweenWindows, 50)
    TrackingWindowMiddleX = TopLeftCornerOfTrackingTaskWindow.X + int(ExperimentSettings.TaskWindowSize.X / 2.0)
    TrackingWindowMiddleY = TopLeftCornerOfTrackingTaskWindow.Y + int(ExperimentSettings.TaskWindowSize.Y / 2.0)
    ScalingJoystickAxis = 5  # how many pixels does the cursor move when joystick is at full angle (value of 1 or -1).
    StepSizeOfTrackingScreenUpdate = 0.005  # how many seconds does it take for a RuntimeVariables.Screen update?


class RuntimeVariables:
    """
    These variables are managed by the program itself.
    Do not modify anything here!
    """
    BlockNumber = 0
    CurrentCircles = []  # is set for each condition
    CurrentTypingTaskNumbers = ""
    CurrentTypingTaskNumbersLength = 1
    CurrentTask = None
    CurrentCursorColor = ExperimentSettings.CursorColorInside
    Conditions = []
    CorrectlyTypedDigitsVisit = 0
    CurrentCondition = ""
    CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)
    CursorDistancesToMiddle = []
    DigitPressTimes = []
    EnteredDigitsStr = ""
    EnvironmentIsRunning = False
    IncorrectlyTypedDigitsTrial = 0
    IncorrectlyTypedDigitsVisit = 0
    IsOutsideRadius = False
    JoystickAxis = Vector2D(0, 0)  # the motion of the joystick
    JoystickObject = None
    LengthOfPathTracked = 0
    MaxPayment = 15
    NumberOfCircleExits = 0
    OutputDataFile = None
    OutputDataFileTrialEnd = None
    Penalty = ""
    ScoresForPayment = []
    Screen = None
    StandardDeviationOfNoise = -1
    StartTimeCurrentTrial = time.time()
    StartTimeOfFirstExperiment = time.time()
    SubjectNumber = 0
    TrackingTaskPresent = False
    TrackingWindowEntryCounter = 0
    TrackingWindowVisible = False
    TrialNumber = 0
    TrialScore = 0
    TypingTaskPresent = False
    TypingWindowEntryCounter = 0
    TypingWindowVisible = False
    VisitEndTime = 0
    VisitScore = 0
    VisitStartTime = 0


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

    if RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask:
        visitTime = time.time() - RuntimeVariables.VisitStartTime
    else:
        visitTime = "-"

    circleRadii = list(map(lambda circle: circle.Radius, RuntimeVariables.CurrentCircles))
    currentTask = str(RuntimeVariables.CurrentTask)

    outputText = \
        str(RuntimeVariables.SubjectNumber) + ";" + \
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
        str(calculateRmse(clearDistances=endOfTrial)) + ";" + \
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
        str(RuntimeVariables.IsOutsideRadius) + ";" + \
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


def calculateRmse(clearDistances):
    """
    The distances are collected each time the cursor changes its position.
    The distances are collected until the RMSE is calculated.
    The RMSE is calculated every time the data file is written.
    The distances are cleared if the parameter is set to True
    """
    n = len(RuntimeVariables.CursorDistancesToMiddle)
    if n == 0:
        return 0
    square = 0

    # Calculate square
    for i in range(0, n):
        square += (RuntimeVariables.CursorDistancesToMiddle[i] ** 2)

    if clearDistances:
        RuntimeVariables.CursorDistancesToMiddle = []

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
                # prevent the program crashing when no joystick is connected
                try:
                    RuntimeVariables.JoystickAxis = Vector2D(RuntimeVariables.JoystickObject.get_axis(0), RuntimeVariables.JoystickObject.get_axis(1))
                except (pygame.error, NameError, AttributeError):
                    pass
        elif event.type == pygame.JOYBUTTONUP and not ExperimentSettings.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTyping")
                writeOutputDataFile("ButtonRelease", "-")
        elif event.type == pygame.JOYBUTTONDOWN and not ExperimentSettings.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1 and RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TypingTaskPresent and not ExperimentSettings.ParallelDualTasks:
                print("PRESSED F1 CLOSE TRACKING")
                switchWindows("openTyping")
                writeOutputDataFile("ButtonRelease", "-")
            elif event.key == pygame.K_F1 and RuntimeVariables.TypingWindowVisible and RuntimeVariables.TrackingTaskPresent and not ExperimentSettings.ParallelDualTasks:
                print("PRESSED F1 OPEN TRACKING")
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")

            if event.key == pygame.K_F4:
                quitApp("F4 was typed to terminate the app")

            # only process keypresses if the digit task is present
            singleTypingTask = RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible
            dualTaskWithSwitching = RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible
            dualTaskParallel = RuntimeVariables.TypingTaskPresent and not RuntimeVariables.TypingWindowVisible and ExperimentSettings.ParallelDualTasks
            if singleTypingTask or dualTaskWithSwitching or dualTaskParallel:
                key = event.unicode
                RuntimeVariables.DigitPressTimes.append(time.time())

                # In parallel dual task, e is to be typed when the cursor was outside the circle. On e, all key presses are neither correct or incorrect.
                if RuntimeVariables.CurrentTypingTaskNumbers[0] == "e" and ExperimentSettings.ParallelDualTasks and (RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask):
                    RuntimeVariables.EnteredDigitsStr += key
                    UpdateTypingTaskString(reset=False)  # generate one new character
                    writeOutputDataFile("keypress", key)
                    print(f"Neutral key press: {key}")
                # If key press is correct ...
                elif key == RuntimeVariables.CurrentTypingTaskNumbers[0]:
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

                if RuntimeVariables.CurrentTask in [TaskTypes.SingleTyping, TaskTypes.PracticeSingleTyping] or not ExperimentSettings.DisplayTypingTaskWithinCursor:
                    drawTypingWindow()


def switchWindows(taskToOpen):
    print("FUNCTION: " + getFunctionName())
    # switching is only done in dual-task
    if RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask:
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


def printTextOverMultipleLines(text, location):
    fontsize = ExperimentSettings.GeneralFontSize
    color = (0, 0, 0)
    pygame.event.pump()
    splittedText = text.split("\n")
    lineDistance = (pygame.font.Font(None, fontsize)).get_linesize()
    PositionX = location[0]
    PositionY = location[1]

    for lines in splittedText:
        f = pygame.font.Font(None, fontsize)
        feedbackmessage = f.render(lines, True, color)
        RuntimeVariables.Screen.blit(feedbackmessage, (PositionX, PositionY))
        PositionY = PositionY + lineDistance


def CountdownMessage(displayTime):
    print("FUNCTION: " + getFunctionName())
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
        printTextOverMultipleLines(message, (topCornerOfMessageArea.X + 45, topCornerOfMessageArea.Y + 10))
        pygame.display.flip()
        time.sleep(1)


def DisplayMessage(message, displayTime):
    print("FUNCTION: " + getFunctionName())
    # prepare background
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))
    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))
    topCornerOfMessageArea = Vector2D(50, 50)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges
    location = Vector2D(topCornerOfMessageArea.X + 75, topCornerOfMessageArea.Y + 75)
    printTextOverMultipleLines(message, (location.X, location.Y))
    pygame.display.flip()
    time.sleep(displayTime)


def drawCanvas():
    print("FUNCTION: " + getFunctionName())
    # prepare background
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))
    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))
    topCornerOfMessageArea = Vector2D(50, 50)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges
    buttonAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 300, Constants.ExperimentWindowSize.Y - 300)).convert()
    buttonAreaObject.fill((150, 150, 150))
    RuntimeVariables.Screen.blit(buttonAreaObject, (150, 150))  # make area 50 pixels away from edges


def reportUserScore():
    print("FUNCTION: " + getFunctionName())
    # prepare background
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))

    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))

    topCornerOfMessageArea = Vector2D(50, 50)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges

    feedbackText = ""
    scoreForLogging = "-"  # score that's logged
    scoresOnThisBlock = []  # stores the scores on the current block. Can be used to report performance each 5th trial

    if RuntimeVariables.CurrentTask == TaskTypes.DualTask:
        feedbackScore = RuntimeVariables.TrialScore
        if RuntimeVariables.TrialScore > 0:
            feedbackText = "+" + str(feedbackScore) + " Punkte"
        else:
            feedbackText = str(feedbackScore) + " Punkte"

        RuntimeVariables.ScoresForPayment.append(RuntimeVariables.TrialScore)
        scoresOnThisBlock.append(RuntimeVariables.TrialScore)  # store score, so average performance can be reported
        scoreForLogging = RuntimeVariables.TrialScore

    elif RuntimeVariables.CurrentTask == TaskTypes.SingleTyping:
        feedbackText = "Anzahl Fehler: \n"
        if RuntimeVariables.TypingTaskPresent:
            digitScore = RuntimeVariables.DigitPressTimes[-1] - RuntimeVariables.DigitPressTimes[0]
            # round values
            digitScore = scipy.special.round(digitScore * 10) / 10
            feedbackText += "\n\n" + str(RuntimeVariables.IncorrectlyTypedDigitsTrial) + " Fehler"
            scoresOnThisBlock.append(RuntimeVariables.IncorrectlyTypedDigitsTrial)
            scoreForLogging = digitScore

    if feedbackText != "":
        location = Vector2D(topCornerOfMessageArea.X + 50, topCornerOfMessageArea.Y + 50)
        printTextOverMultipleLines(feedbackText, (location.X, location.Y))

    pygame.display.flip()
    writeOutputDataFile("scoreGiven", str(scoreForLogging))
    time.sleep(ExperimentSettings.TimeFeedbackIsGiven)

    if len(scoresOnThisBlock) % 5 == 0:  # every fifth trial, report mean score
        # prepare background
        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))
        messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
        messageAreaObject.fill((255, 255, 255))
        topCornerOfMessageArea = Vector2D(50, 50)
        RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges

        feedbackText2 = "Deine durchschnittliche Punktzahl der letzten 4 Durchgänge:\n\n"
        meanscore = scipy.special.round(scipy.mean(scoresOnThisBlock[-2:]) * 100) / 100  # report meanscore
        feedbackText2 = feedbackText2 + str(meanscore)

        if RuntimeVariables.CurrentTask == TaskTypes.SingleTracking:
            feedbackText2 = feedbackText2 + " pixels"
        elif RuntimeVariables.CurrentTask == TaskTypes.SingleTyping:
            feedbackText2 = feedbackText2 + " errors"
        elif RuntimeVariables.CurrentTask == TaskTypes.DualTask:
            feedbackText2 = "Block " + str(int(len(scoresOnThisBlock) / 3)) + " von 6 vollständig. Deine durchschnittliche Leistung der letzten 4 Durchgänge:\n\n" + str(meanscore) + " points"

        location = Vector2D(topCornerOfMessageArea.X + 50, topCornerOfMessageArea.Y + 50)

        printTextOverMultipleLines(feedbackText2, (location.X, location.Y))
        pygame.display.flip()

        writeOutputDataFile("avscoreGiven", str(meanscore))
        time.sleep(20)


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
    print("FUNCTION: " + getFunctionName())

    # For single typing task or regular dual task with switching, return the single task string
    isSwitchingDualTask = RuntimeVariables.CurrentTask in [TaskTypes.DualTask, TaskTypes.PracticeDualTask] and not ExperimentSettings.ParallelDualTasks
    isSingleTypingTask = RuntimeVariables.CurrentTask in [TaskTypes.SingleTyping, TaskTypes.PracticeSingleTyping]
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
    if not possibleCharacters and ExperimentSettings.ParallelDualTasks:
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


def drawCursor(sleepTime):
    restSleepTime = 0
    x = RuntimeVariables.CursorCoordinates.X
    y = RuntimeVariables.CursorCoordinates.Y
    oldX = x
    oldY = y
    final_x = x
    final_y = y

    # only add noise if tracking is not moving
    motionThreshold = 0.08

    joystickAxisWithinThreshold = RuntimeVariables.JoystickAxis.X > motionThreshold or \
                                  RuntimeVariables.JoystickAxis.X < -motionThreshold or \
                                  RuntimeVariables.JoystickAxis.Y > motionThreshold or \
                                  RuntimeVariables.JoystickAxis.Y < -motionThreshold

    if not (RuntimeVariables.TrackingWindowVisible and joystickAxisWithinThreshold):
        final_x = x + random.gauss(0, RuntimeVariables.StandardDeviationOfNoise)
        final_y = y + random.gauss(0, RuntimeVariables.StandardDeviationOfNoise)

    if RuntimeVariables.TrackingWindowVisible:  # only add RuntimeVariables.JoystickAxis if the window is open (i.e., if the participant sees what way cursor moves!)
        final_x += RuntimeVariables.JoystickAxis.X * Constants.ScalingJoystickAxis
        final_y += RuntimeVariables.JoystickAxis.Y * Constants.ScalingJoystickAxis

    # now iterate through updates (but only do that if the window is open - if it's closed do it without mini-steps, so as to make computation faster)
    nrUpdates = int(sleepTime / Constants.StepSizeOfTrackingScreenUpdate)
    delta_x = (final_x - x) / nrUpdates
    delta_y = (final_y - y) / nrUpdates

    if RuntimeVariables.TrackingWindowVisible:
        for i in range(0, nrUpdates):
            x += delta_x
            y += delta_y

            if (x, y) != RuntimeVariables.CursorCoordinates:
                # now check if the cursor is still within RuntimeVariables.Screen range
                if x < (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2):
                    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2
                elif x > (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2):
                    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2

                if y < (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2):
                    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2
                elif y > (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2):
                    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2

                # always update coordinates
                RuntimeVariables.CursorCoordinates = Vector2D(x, y)

                if RuntimeVariables.TrackingWindowVisible:  # only update screen when it's visible
                    distanceCursorMiddle = math.sqrt((abs(Constants.TrackingWindowMiddleX - x)) ** 2 + (abs(Constants.TrackingWindowMiddleY - y)) ** 2)
                    largestCircleRadius = max(list(map(lambda circle: circle.Radius, RuntimeVariables.CurrentCircles)))
                    wasCursorOutsideRadiusBefore = RuntimeVariables.IsOutsideRadius
                    if distanceCursorMiddle > largestCircleRadius:
                        RuntimeVariables.IsOutsideRadius = True
                        RuntimeVariables.CurrentCursorColor = ExperimentSettings.CursorColorInside
                        # When the cursor moves outside the circles, the parallel dual task typing number shall become "e" immediately
                        if not wasCursorOutsideRadiusBefore and ExperimentSettings.ParallelDualTasks:
                            RuntimeVariables.CurrentTypingTaskNumbers = "e"
                    else:
                        RuntimeVariables.IsOutsideRadius = False
                        RuntimeVariables.CurrentCursorColor = ExperimentSettings.CursorColorOutside
                        # When the cursor moves back inside the circles, the parallel dual task typing number shall become a number immediately
                        if wasCursorOutsideRadiusBefore and ExperimentSettings.ParallelDualTasks and not RuntimeVariables.CurrentTask in [TaskTypes.SingleTracking, TaskTypes.PracticeSingleTracking]:
                            UpdateTypingTaskString(reset=False)

                    drawTrackingWindow()

            time.sleep(Constants.StepSizeOfTrackingScreenUpdate)

        # see if there is additional time to sleep
        mods = sleepTime % Constants.StepSizeOfTrackingScreenUpdate
        if mods != 0:
            restSleepTime = mods

    # if tracking window is not visible, just update the values
    else:
        x = final_x
        y = final_y

        # now check if the cursor is still within RuntimeVariables.Screen range
        if (x, y) != RuntimeVariables.CursorCoordinates:
            if x < (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2):
                x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2
            elif x > (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2):
                x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2

            if y < (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2):
                y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2
            elif y > (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2):
                y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2
        # if display is not updated, sleep for entire time
        restSleepTime = sleepTime

    # always update coordinates
    RuntimeVariables.CursorCoordinates = Vector2D(x, y)

    # collect distances of the cursor to the circle middle for the RMSE
    RuntimeVariables.CursorDistancesToMiddle.append(math.sqrt((Constants.TrackingWindowMiddleX - x) ** 2 + (Constants.TrackingWindowMiddleY - y) ** 2))

    # collect cumulatively the distance the cursor has moved
    RuntimeVariables.LengthOfPathTracked += math.sqrt((oldX - x) ** 2 + (oldY - y) ** 2)

    return restSleepTime


def drawTypingTaskWithinCursor():
    fontsize = ExperimentSettings.FontSizeTypingTaskNumberWithinCursor
    f = pygame.font.Font(None, fontsize)
    typingTaskNumberText = f.render(RuntimeVariables.CurrentTypingTaskNumbers, True, ExperimentSettings.FontColorTypingTaskNumberWithinCursor)
    textWidth, textHeight = f.size(RuntimeVariables.CurrentTypingTaskNumbers)
    x = RuntimeVariables.CursorCoordinates.X - (textWidth / 2)
    y = RuntimeVariables.CursorCoordinates.Y - (textHeight / 2)
    RuntimeVariables.Screen.blit(typingTaskNumberText, (x, y))


def closeTypingWindow():
    print("FUNCTION: " + getFunctionName())
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
    RuntimeVariables.Screen.blit(bg, (location.X, location.Y))  # make area about 30 away from centre


def openTypingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.VisitStartTime = time.time()
    RuntimeVariables.IsOutsideRadius = False
    RuntimeVariables.CorrectlyTypedDigitsVisit = 0
    RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
    RuntimeVariables.TypingWindowEntryCounter = RuntimeVariables.TypingWindowEntryCounter + 1
    drawTypingWindow()
    RuntimeVariables.TypingWindowVisible = True


def drawTypingWindow():
    # draw background
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
    RuntimeVariables.Screen.blit(bg, (Constants.TopLeftCornerOfTypingTaskWindow.X, Constants.TopLeftCornerOfTypingTaskWindow.Y))  # make area about 30 away from centre

    if not ExperimentSettings.ParallelDualTasks and (RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask):
        drawCover("tracking")

    fontsize = ExperimentSettings.FontSizeTypingTaskNumberSingleTask
    f = pygame.font.Font(None, fontsize)
    typingTaskNumberText = f.render(RuntimeVariables.CurrentTypingTaskNumbers, True, (0, 0, 0))
    textWidth, textHeight = f.size(RuntimeVariables.CurrentTypingTaskNumbers)
    x = (Constants.TopLeftCornerOfTypingTaskWindow.X + ExperimentSettings.TaskWindowSize.X / 2) - (textWidth / 2)
    y = (Constants.TopLeftCornerOfTypingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y / 2) - (textHeight / 2)
    RuntimeVariables.Screen.blit(typingTaskNumberText, (x, y))


def closeTrackingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.TrackingWindowVisible = False
    RuntimeVariables.VisitEndTime = time.time()


def openTrackingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.VisitStartTime = time.time()
    RuntimeVariables.TrackingWindowEntryCounter += 1

    if RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask:
        updateScore()

    RuntimeVariables.TrackingWindowVisible = True

    # get the cursor angle
    # prevent the program crashing when no joystick is connected
    try:
        RuntimeVariables.JoystickAxis = Vector2D(RuntimeVariables.JoystickObject.get_axis(0), RuntimeVariables.JoystickObject.get_axis(1))
    except (pygame.error, NameError, AttributeError):
        pass


def drawTrackingWindow():
    # draw background
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
    drawCircles(bg)
    RuntimeVariables.Screen.blit(bg, (Constants.TopLeftCornerOfTrackingTaskWindow.X, Constants.TopLeftCornerOfTrackingTaskWindow.Y))  # make area about 30 away from centre
    newCursorLocation = Vector2D(RuntimeVariables.CursorCoordinates.X - (ExperimentSettings.CursorSize.X / 2), RuntimeVariables.CursorCoordinates.Y - (ExperimentSettings.CursorSize.Y / 2))
    newCursor = pygame.Surface((ExperimentSettings.CursorSize.X, ExperimentSettings.CursorSize.Y)).convert()
    newCursor.fill(RuntimeVariables.CurrentCursorColor)
    RuntimeVariables.Screen.blit(newCursor, (newCursorLocation.X, newCursorLocation.Y))  # blit puts something new on the RuntimeVariables.Screen

    # Show the number of points above the tracking circle
    if RuntimeVariables.Penalty != "none" and (RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask) and not ExperimentSettings.ParallelDualTasks:
        drawDualTaskScore()


def drawDualTaskScore():
    intermediateMessage = str(RuntimeVariables.VisitScore) + " Punkte"
    fontsize = ExperimentSettings.GeneralFontSize
    f = pygame.font.Font(None, fontsize)
    textWidth, textHeight = f.size(intermediateMessage)
    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + (ExperimentSettings.TaskWindowSize.X / 2) - (textWidth / 2)
    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + 10
    printTextOverMultipleLines(intermediateMessage, (x, y))


def updateScore():
    print("FUNCTION: " + getFunctionName())
    if RuntimeVariables.Penalty == "none":
        RuntimeVariables.VisitScore = 0
    elif RuntimeVariables.IsOutsideRadius:
        RuntimeVariables.NumberOfCircleExits += 1
        if RuntimeVariables.Penalty == "lose500":
            # loose 500
            RuntimeVariables.VisitScore = ((RuntimeVariables.CorrectlyTypedDigitsVisit + 10) + (RuntimeVariables.IncorrectlyTypedDigitsVisit - 5)) - 500

        if RuntimeVariables.Penalty == "loseAll":
            # loose all
            RuntimeVariables.VisitScore = 0

        if RuntimeVariables.Penalty == "loseHalf":
            # loose half
            RuntimeVariables.VisitScore = 0.5 * ((RuntimeVariables.CorrectlyTypedDigitsVisit * 10) + (RuntimeVariables.IncorrectlyTypedDigitsVisit * -5))  # RuntimeVariables.Penalty for exit is to lose half points
    else:
        RuntimeVariables.VisitScore = (RuntimeVariables.CorrectlyTypedDigitsVisit * 10) + (RuntimeVariables.IncorrectlyTypedDigitsVisit * -5)  # gain is 10 for correct digit and -5 for incorrect digit

    # add the score for this digit task visit to the overall trial score
    # duringtrial score is used in reportUserScore
    RuntimeVariables.TrialScore += RuntimeVariables.VisitScore
    writeOutputDataFile("updatedVisitScore", str(RuntimeVariables.VisitScore))
    RuntimeVariables.IsOutsideRadius = False


def runSingleTaskTypingTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTask = TaskTypes.PracticeSingleTyping
        DisplayMessage("Nur Tippen\n\n"
                       "In diesen Durchgängen übst du nur die Tippaufgabe.\n"
                       "Kopiere die Ziffern, die dir auf dem Bildschirm angezeigt werden so schnell wie möglich.\n\n"
                       "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n"
                       "(In zukünftigen Durchgängen würdest du dadurch Punkte verlieren.)", 15)
    else:
        RuntimeVariables.CurrentTask = TaskTypes.SingleTyping
        DisplayMessage("Nur Tippen\n\n"
                       "Kopiere die Ziffern so schnell wie möglich.\n"
                       "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n", 10)

    RuntimeVariables.CurrentTypingTaskNumbersLength = ExperimentSettings.SingleTypingTaskNumbersLength

    for i in range(0, numberOfTrials):
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0

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
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates
            pygame.display.flip()
            time.sleep(0.02)

        if (time.time() - RuntimeVariables.StartTimeCurrentTrial) >= ExperimentSettings.MaxTrialTimeSingleTyping:
            writeOutputDataFile("trialStopTooMuchTime", "-", True)
        elif not RuntimeVariables.EnvironmentIsRunning:
            writeOutputDataFile("trialStopEnvironmentStopped", "-", True)
        else:
            writeOutputDataFile("trialStop", "-", True)

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def runSingleTaskTrackingTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTask = TaskTypes.PracticeSingleTracking
        DisplayMessage(
            "Nur Tracking\n\n"
            "In diesen Durchgängen übst du nur die Trackingaufgabe.\n"
            "Du kannst ausprobieren, wie der Joystick funktioniert und sehen, wie schnell der blaue Cursor umherwandert.\n"
            "Der Cursor bewegt sich so lange frei herum, bis du ihn mit dem Joystick bewegst.\n"
            "Denk daran: deine Aufgabe ist es, zu verhindern, dass der blaue Cursor den Kreis verlässt!",
            15)
    else:
        RuntimeVariables.CurrentTask = TaskTypes.SingleTracking
        DisplayMessage(
            "Nur Tracking\n\n"
            "Nutze diesen Durchgang, um dich mit der Geschwindigkeit des Cursors vertraut zu machen, \n"
            "und denk daran den Cursor mit deinem Joystick in der Kreismitte zu halten.",
            10)

    for i in range(0, numberOfTrials):
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

            restSleepTime = 0
            if RuntimeVariables.TrackingTaskPresent and RuntimeVariables.TrackingWindowVisible:
                drawTrackingWindow()
                restSleepTime = drawCursor(0.02)
                writeOutputDataFile("trackingVisible", "-")

            pygame.display.flip()
            time.sleep(restSleepTime)

        if not RuntimeVariables.EnvironmentIsRunning:
            writeOutputDataFile("trialEnvironmentRunning", "-", True)
        else:
            writeOutputDataFile("trialEnvironmentStopped", "-", True)


def runDualTaskTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTask = TaskTypes.PracticeDualTask
        message = "Tracking + Tippen (MULTITASKING)\n\n" \
                  "Du übst jetzt beide Aufgaben gleichzeitig!\n\n"
        if not ExperimentSettings.ParallelDualTasks:
            message += "Die Ziffernaufgabe wird dir immer zuerst angezeigt.\n" \
                       "Drücke den Schalter unter deinem Zeigefinger am Joystick, um zu kontrollieren ob der blaue Cursor\n" \
                       "noch innerhalb des Kreises ist.\n" \
                       "Lasse den Schalter wieder los, um zur Ziffernaufgabe zurück zu gelangen.\n" \
                       "Du kannst immer nur eine Aufgabe bearbeiten."
        DisplayMessage("Dein Ziel:\n\n"
                       "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte,\n"
                       "aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
                       "Fehler beim Tippen führen auch zu Punktverlust.", 10)
    else:
        RuntimeVariables.CurrentTask = TaskTypes.DualTask
        DisplayMessage("Tracking + Tippen (MULTITASKING)\n\n"
                       "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte,\n"
                       "aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
                       "Fehler beim Tippen führen auch zu einem Punktverlust.\n\n"
                       "Wichtig: Deine Leistung in diesen Durchgängen zählt für deine Gesamtpunktzahl.", 18)
        if not ExperimentSettings.ParallelDualTasks:
            DisplayMessage("Drücke den Schalter unter deinem Zeigefinger, um das Trackingfenster zu öffnen.\n"
                           "Um wieder zurück zur Tippaufgabe zu gelangen, lässt du den Schalter wieder los.\n"
                           "Du kannst immer nur eine Aufgabe bearbeiten.", 15)

    RuntimeVariables.CurrentTypingTaskNumbersLength = 1 if ExperimentSettings.ParallelDualTasks else ExperimentSettings.SingleTypingTaskNumbersLength

    for i in range(0, numberOfTrials):
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        RuntimeVariables.IsOutsideRadius = False
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0

        CountdownMessage(3)
        pygame.event.clear()  # clear all events

        if ExperimentSettings.DisplayTypingTaskWithinCursor:
            RuntimeVariables.TrackingWindowVisible = True
            RuntimeVariables.TypingWindowVisible = False
        elif ExperimentSettings.ParallelDualTasks:
            RuntimeVariables.TrackingWindowVisible = True
            RuntimeVariables.TypingWindowVisible = True
        else: # normal dual task with switching
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
            #restSleepTime = 0
            restSleepTime = drawCursor(0.02)  # also draws tracking window
            if RuntimeVariables.TrackingTaskPresent and RuntimeVariables.TrackingWindowVisible:
                #drawTrackingWindow()
                if not ExperimentSettings.ParallelDualTasks:
                    drawCover("typing")
                if ExperimentSettings.DisplayTypingTaskWithinCursor and ExperimentSettings.ParallelDualTasks:
                    drawTypingTaskWithinCursor()
            if ExperimentSettings.ParallelDualTasks and RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible and not ExperimentSettings.DisplayTypingTaskWithinCursor:
                drawTypingWindow()

            pygame.display.flip()
            time.sleep(restSleepTime)

            if ExperimentSettings.ParallelDualTasks:
                eventMsg = "trackingAndTypingVisible"
            elif RuntimeVariables.TrackingWindowVisible:
                eventMsg = "trackingVisible"
            elif RuntimeVariables.TypingWindowVisible:
                eventMsg = "typingVisible"
            else:
                eventMsg = ""

            writeOutputDataFile(eventMsg, "-")

        RuntimeVariables.VisitEndTime = time.time()
        updateScore()

        if (time.time() - RuntimeVariables.StartTimeCurrentTrial) >= ExperimentSettings.MaxTrialTimeDual:
            writeOutputDataFile("trialStopTooMuchTime", "-", True)
        elif not RuntimeVariables.EnvironmentIsRunning:
            writeOutputDataFile("trialStopEnvironmentStopped", "-", True)
        else:
            writeOutputDataFile("trialStop", "-", True)

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def initializeOutputFiles(subjNrStr):
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
        "RuntimeExperimentVariables.CurrentTypingTaskNumbers" + ";" \
        "GeneratedTypingTaskNumberLength" + ";" \
        "NumberOfCircleExits" + ";" \
        "TrialScore" + ";" \
        "VisitScore" + ";" \
        "CorrectDigitsVisit" + ";" \
        "IncorrectDigitsVisit" + ";" \
        "IncorrectDigitsTrial" + ";" \
        "OutsideRadius" + ";" \
        "EventMessage1" + ";" \
        "EventMessage2" + "\n"

    timestamp = time.strftime("%Y-%m-%d_%H-%M")
    dataFileName = "participant_" + subjNrStr + "_data_" + timestamp + ".csv"
    RuntimeVariables.OutputDataFile = open(dataFileName, 'w')  # contains the user data
    RuntimeVariables.OutputDataFile.write(outputText)
    RuntimeVariables.OutputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFile.fileno())

    summaryFileName = "participant_" + subjNrStr + "_data_lastTrialEntry_" + timestamp + ".csv"
    RuntimeVariables.OutputDataFileTrialEnd = open(summaryFileName, 'w')  # contains the user data
    RuntimeVariables.OutputDataFileTrialEnd.write(outputText)
    RuntimeVariables.OutputDataFileTrialEnd.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFileTrialEnd.fileno())


def readConditionFile(subjNrStr):
    """
    Read the participant file
    """
    f = open('participantConditions.csv', 'r')
    individualLines = f.read().split('\n')  ## read by lines
    lines = list(map(lambda x: x.split(';'), individualLines))  # split all elements
    subjectLine = []
    for line in lines:
        if line[0] == subjNrStr:
            if not subjectLine:
                subjectLine = line[1:]
            else:
                raise Exception("Duplicate subject number")
    if not subjectLine:
        raise Exception("Invalid subject number")
    RuntimeVariables.Conditions = subjectLine
    f.close()


def ShowStartExperimentScreen():
    drawCanvas()
    location = Vector2D(175, 175)

    message = "Experimentalleiter bitte hier drücken."
    printTextOverMultipleLines(message, (location.X, location.Y))
    pygame.display.flip()

    while not checkMouseClicked():  # wait for a mouseclick
        time.sleep(0.25)
    RuntimeVariables.StartTimeCurrentTrial = time.time()


def StartExperiment():
    # Sort the circle lists by radius to make getting the typing task numbers work properly
    ExperimentSettings.CirclesSmall.sort(key=lambda circle: circle.Radius, reverse=False)
    ExperimentSettings.CirclesBig.sort(key=lambda circle: circle.Radius, reverse=False)
    ExperimentSettings.CirclesPractice.sort(key=lambda circle: circle.Radius, reverse=False)

    ValidateExperimentSettings()

    subjNrStr = input("Please enter the subject number here: ")
    RuntimeVariables.SubjectNumber = int(subjNrStr)

    firstTrialInput = input("First trial? (yes/no) ")
    if firstTrialInput != "yes" and firstTrialInput != "no":
        raise Exception("Invalid input '" + firstTrialInput + "'. Allowed is 'yes' or 'no' only.")

    showPrecedingPenaltyInfo = input("Show reward, penalty and noise information before the experiment starts? (yes/no) ")
    if showPrecedingPenaltyInfo != "yes" and showPrecedingPenaltyInfo != "no":
        raise Exception("Invalid input '" + showPrecedingPenaltyInfo + "'. Allowed is 'yes' or 'no' only.")

    readConditionFile(subjNrStr)
    initializeOutputFiles(subjNrStr)
    RuntimeVariables.StartTimeOfFirstExperiment = time.time()

    pygame.init()
    if ExperimentSettings.Fullscreen:
        RuntimeVariables.Screen = pygame.display.set_mode((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y), pygame.FULLSCREEN)
    else:
        RuntimeVariables.Screen = pygame.display.set_mode((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y))
    pygame.display.set_caption(Constants.Title)
    RuntimeVariables.EnvironmentIsRunning = True

    ShowStartExperimentScreen()
    RuntimeVariables.StartTime = time.time()

    # verify all RuntimeVariables.Conditions before the experiment starts so that the program would crash at the start if it does
    conditionsVerified = []
    for pos in range(0, len(RuntimeVariables.Conditions)):
        currentCondition = RuntimeVariables.Conditions[pos]
        numDigits = len(currentCondition)
        if numDigits != 3:
            raise Exception("Current Condition" + currentCondition + " has invalid length " + str(len(currentCondition)))

        # noise values are h (high), m (medium) or l (low)
        if currentCondition[0] == "h":
            RuntimeVariables.StandardDeviationOfNoise = ExperimentSettings.CursorNoises["high"]
            noiseMsg = "hoher"
        elif currentCondition[0] == "m":
            RuntimeVariables.StandardDeviationOfNoise = ExperimentSettings.CursorNoises["medium"]
            noiseMsg = "mittlerer"
        elif currentCondition[0] == "l":
            RuntimeVariables.StandardDeviationOfNoise = ExperimentSettings.CursorNoises["low"]
            noiseMsg = "niedriger"
        else:
            raise Exception("Invalid noise " + currentCondition[0])

        # radius is S (small) or B (big)
        if currentCondition[1] == "S":  # small radius
            radiusCircle = ExperimentSettings.CirclesSmall
        elif currentCondition[1] == "B":
            radiusCircle = ExperimentSettings.CirclesBig
        else:
            raise Exception("Invalid radius " + currentCondition[1])

        # only if the fourth digit is specified, define RuntimeVariables.Penalty
        if currentCondition[2] == "a":
            RuntimeVariables.Penalty = "loseAll"
            penaltyMsg = "alle"
        elif currentCondition[2] == "h":
            RuntimeVariables.Penalty = "loseHalf"
            penaltyMsg = "die Hälfte deiner"
        elif currentCondition[2] == "n":
            RuntimeVariables.Penalty = "lose500"
            penaltyMsg = "500"
        elif currentCondition[2] == "-":
            RuntimeVariables.Penalty = "none"
            penaltyMsg = "-"
        else:
            raise Exception("Invalid RuntimeVariables.Penalty " + currentCondition[2])

        conditionsVerified.append({
            "RuntimeVariables.StandardDeviationOfNoise": RuntimeVariables.StandardDeviationOfNoise,
            "noiseMsg": noiseMsg,
            "radiusCircle": radiusCircle,
            "RuntimeVariables.Penalty": RuntimeVariables.Penalty,
            "penaltyMsg": penaltyMsg
        })

    if firstTrialInput == "yes":
        DisplayMessage("Willkommen zum Experiment!\n\n\n"
                       "Wir beginnen mit den Übungsdurchläufen.", 10)

        # do practice trials
        RuntimeVariables.CurrentCircles = ExperimentSettings.CirclesPractice
        for block in ExperimentSettings.RunningOrder:
            if block.TaskType == TaskTypes.PracticeSingleTracking:
                runSingleTaskTrackingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeSingleTyping:
                runSingleTaskTypingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeDualTask:
                runDualTaskTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)

        DisplayMessage("Nun beginnt der Hauppteil und wir testen deine Leistung in den Aufgaben, die du \n"
                       "gerade geübt hast.\n"
                       "Versuche im Laufe des Experiments so viele Punkte wie möglich zu gewinnen!", 10)

    # main experiment loop with verified RuntimeVariables.Conditions
    for condition in conditionsVerified:
        print("condition: " + str(condition))
        # set global and local variables
        RuntimeVariables.StandardDeviationOfNoise = condition["RuntimeVariables.StandardDeviationOfNoise"]
        noiseMsg = condition["noiseMsg"]
        RuntimeVariables.CurrentCircles = condition["radiusCircle"]
        RuntimeVariables.Penalty = condition["RuntimeVariables.Penalty"]
        penaltyMsg = condition["penaltyMsg"]

        for block in ExperimentSettings.RunningOrder:
            if block.TaskType == TaskTypes.SingleTracking:
                message = getMessageBeforeTrial(TaskTypes.SingleTracking, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo)
                DisplayMessage(message, 12)
                runSingleTaskTrackingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.SingleTyping:
                message = getMessageBeforeTrial(TaskTypes.SingleTyping, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo)
                DisplayMessage(message, 12)
                runSingleTaskTypingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.DualTask:
                message = getMessageBeforeTrial(TaskTypes.DualTask, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo)
                DisplayMessage(message, 12)
                runDualTaskTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)

        message = "Bisher hast du: " + str(scipy.sum(RuntimeVariables.ScoresForPayment)) + " Punkte"
        DisplayMessage(message, 8)

    DisplayMessage("Dies ist das Ende der Studie.", 10)
    quitApp()


def ValidateExperimentSettings():
    """Some important consistency checks for fields of GeneralExperimentSettings"""
    for block in ExperimentSettings.RunningOrder:
        if block.TaskType.name not in TaskTypes._member_names_:
            quitApp(f"Specified TaskType {block.TaskType} is invalid!")
    if ExperimentSettings.DisplayTypingTaskWithinCursor and not ExperimentSettings.ParallelDualTasks:
        quitApp("If you set DisplayTypingTaskWithinCursor to True, you also have to set ParallelDualTasks to True!")


def getMessageBeforeTrial(trialType, noiseMsg, penaltyMsg, showPrecedingPenaltyInfo):
    message = "NEUER BLOCK: \n\n\n"
    if trialType == TaskTypes.SingleTracking or trialType == TaskTypes.DualTask:
        message += "In den folgenden Durchgängen bewegt sich der Cursor mit " + noiseMsg + " Geschwindigkeit. \n"
    if trialType == TaskTypes.SingleTyping or trialType == TaskTypes.DualTask:
        message += "Für jede korrekt eingegebene Ziffer bekommst du 10 Punkte. \n"
    if showPrecedingPenaltyInfo == "yes":
        if trialType == TaskTypes.SingleTyping or trialType == TaskTypes.DualTask:
            message += "Bei jeder falsch eingetippten Ziffer verlierst du 5 Punkte. \n"
        if trialType == TaskTypes.SingleTracking or trialType == TaskTypes.DualTask:
            message += "Achtung: Wenn der Cursor den Kreis verlässt, verlierst du " + penaltyMsg + " deiner Punkte."
    elif showPrecedingPenaltyInfo == "no":
        if trialType == TaskTypes.DualTask:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern und wenn der Punkt den Kreis verlässt."
        elif trialType == TaskTypes.SingleTyping:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern."
        elif trialType == TaskTypes.SingleTracking:
            message += "Achtung: Du verlierst Punkte wenn der Punkt den Kreis verlässt."
    return message


def quitApp(message=None):
    if message:
        print(message)
    RuntimeVariables.EnvironmentIsRunning = False
    pygame.display.quit()
    pygame.quit()
    try:
        RuntimeVariables.OutputDataFile.close()
        RuntimeVariables.OutputDataFileTrialEnd.close()
    except NameError:
        pass
    sys.exit()


def getFunctionName():
    return inspect.stack()[1][3]


if __name__ == '__main__':
    try:
        StartExperiment()
    except Exception as e:
        stack = traceback.format_exc()
        with open("Error_Logfile.txt", "a") as log:
            log.write(f"{datetime.datetime.now()} {str(e)}   {str(stack)} \n")
            print(str(e))
            print(str(stack))
            print("PLEASE CHECK Error_Logfile.txt, the error is logged there!")
